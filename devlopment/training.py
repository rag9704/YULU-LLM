import torch
import intel_extension_for_pytorch as ipex
from bigdl.llm.transformers import AutoModelForCausalLM
from bigdl.llm.transformers.qlora import (
    get_peft_model,
    prepare_model_for_kbit_training as prepare_model,
)
from peft import LoraConfig
from bigdl.llm.transformers.qlora import PeftModel
import transformers
from transformers import (
    DataCollatorForSeq2Seq,
    LlamaTokenizer,
    AutoTokenizer,
    Trainer,
    TrainingArguments,
)

BASE_MODELS = {
    "0": "mistralai/Mistral-7B-Instruct-v0.1",  # https://huggingface.co/NousResearch/Nous-Hermes-llama-2-7b
}
BASE_MODEL = BASE_MODELS["0"]
DATA_PATH = "./training_instruct.csv"

MODEL_PATH = "./final_model"
ADAPTER_PATH = "./lora_adapters"
DEVICE = torch.device("xpu" if torch.xpu.is_available() else "cpu")
LORA_CONFIG = LoraConfig(
    r=16,  # rank
    lora_alpha=32,  # scaling factor
    target_modules=[
        "q_proj",
        "k_proj",
        "v_proj",
        "o_proj",
        "gate_proj",
        "up_proj",
        "down_proj",
        "lm_head",
    ], 
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM",
)
MODEL_CACHE_PATH = "/home/common/data/Big_Data/GenAI/llm_models"

print("=" * 80)
print(f"Using Device: {DEVICE}")
print(f"Final model will be saved to: {MODEL_PATH}")
print(f"LoRA adapters will be saved to: {ADAPTER_PATH}")
print(f"Finetuning Model: {BASE_MODEL}")
print(f"Using dataset from: {DATA_PATH}")
print(f"Model cache: {MODEL_CACHE_PATH}")
print("=" * 80)

def generate_prompt(input_question, context, output=""):
    """
    Generates a prompt for fine-tuning the LLM model for text-to-SQL tasks.

    Parameters:
        input_question (str): The input text or question to be converted to SQL.
        context (str): The schema or context in which the SQL query operates.
        output (str, optional): The expected SQL query as the output.

    Returns:
        str: A formatted string serving as the prompt for the fine-tuning task.
    """
    


    
    return f"""You are powerfull

### Input:
{input_question}

### Context:
{context}

### Response:
{output}"""




def setup_model_and_tokenizer(base_model_id: str):
    """Downloads / Loads the pre-trained model in NF4 datatype and tokenizer based on the given base model ID for training."""
    local_model_id = base_model_id.replace("/", "--")
    local_model_path = os.path.join(MODEL_CACHE_PATH, local_model_id)
    print(f"local model path is: {local_model_path}")

    try:
        model = AutoModelForCausalLM.from_pretrained(
            local_model_path,
            load_in_low_bit="nf4",
            optimize_model=False,
            torch_dtype=torch.float16,
            modules_to_not_convert=["lm_head"],
        )
    except OSError as e:
        print(e)
        sys.exit()
        logging.info(
            f"Model not found locally. Downloading {base_model_id} to cache..."
        )
        model = AutoModelForCausalLM.from_pretrained(
            base_model_id,
            load_in_low_bit="nf4",
            optimize_model=False,
            torch_dtype=torch.float16,
            modules_to_not_convert=["lm_head"],
        )

    try:
        if "llama" in base_model_id.lower():
            tokenizer = LlamaTokenizer.from_pretrained(local_model_path)
        else:
            tokenizer = AutoTokenizer.from_pretrained(local_model_path)
    except OSError:
        logging.info(
            f"Tokenizer not found locally. Downloading tokenizer for {base_model_id} to cache..."
        )
        if "llama" in base_model_id.lower():
            tokenizer = LlamaTokenizer.from_pretrained(base_model_id)
        else:
            tokenizer = AutoTokenizer.from_pretrained(base_model_id)
    tokenizer.pad_token_id = 0
    tokenizer.padding_side = "left"
    return model, tokenizer


class FineTuner:
    """A class to handle the fine-tuning of LLM models."""

    def __init__(self, base_model_id: str, model_path: str, device: torch.device):
        """
        Initialize the FineTuner with base model, model path, and device.

        Parameters:
            base_model_id (str): Id of pre-trained model to use for fine-tuning.
            model_path (str): Path to save the fine-tuned model.
            device (torch.device): Device to run the model on.
        """
        self.base_model_id = base_model_id
        self.model_path = model_path
        self.device = device
        self.model, self.tokenizer = setup_model_and_tokenizer(base_model_id)


    def tokenize_data(
        self, data_points, add_eos_token=True, train_on_inputs=False, cutoff_len=512
    ) -> dict:
        """
        Tokenizes dataset of SQL related data points consisting of questions, context, and answers.

        Parameters:
            data_points (dict): A batch from the dataset containing 'question', 'context', and 'answer'.
            add_eos_token (bool): Whether to add an EOS token at the end of each tokenized sequence.
            cutoff_len (int): The maximum length for each tokenized sequence.

        Returns:
            dict: A dictionary containing tokenized 'input_ids', 'attention_mask', and 'labels'.
        """
        try:
            #question = data_points["input"]
            #context = data_points["instruction"]
            #answer = data_points["ouput"]
            data =  data_points['Instruct']
            if train_on_inputs:
                #user_prompt = generate_prompt(question, context)
                user_prompt = data
                tokenized_user_prompt = self.tokenizer(
                    user_prompt,
                    truncation=True,
                    max_length=cutoff_len,
                    padding=False,
                    return_tensors=None,
                )
                user_prompt_len = len(tokenized_user_prompt["input_ids"])
                if add_eos_token:
                    user_prompt_len -= 1

            combined_text = data
            tokenized = self.tokenizer(
                combined_text,
                truncation=True,
                max_length=cutoff_len,
                padding=False,
                return_tensors=None,
            )
            if (
                tokenized["input_ids"][-1] != self.tokenizer.eos_token_id
                and add_eos_token
                and len(tokenized["input_ids"]) < cutoff_len
            ):
                tokenized["input_ids"].append(self.tokenizer.eos_token_id)
                tokenized["attention_mask"].append(1)
            tokenized["labels"] = tokenized["input_ids"].copy()
            if train_on_inputs:
                tokenized["labels"] = [-100] * user_prompt_len + tokenized["labels"][
                    user_prompt_len:
                ]

            return tokenized
        except Exception as e:
            logging.error(
                f"Error in batch tokenization: {e}, Line: {e.__traceback__.tb_lineno}"
            )
            raise e

    def prepare_data(self, data, val_set_size=
                     ) -> Dataset:
        """Prepare training and validation datasets."""
        try:
            train_val_split = data["train"].train_test_split(
                test_size=val_set_size, shuffle=True, seed=42
            )
            train_data = train_val_split["train"].shuffle().map(self.tokenize_data)
            val_data = train_val_split["test"].shuffle().map(self.tokenize_data)
            return train_data, val_data
        except Exception as e:
            logging.error(
                f"Error in preparing data: {e}, Line: {e.__traceback__.tb_lineno}"
            )
            raise e

    def train_model(self, train_data, training_args):
        """
        Fine-tune the model with the given training and validation data.

        Parameters:
            train_data (Dataset): Training data.
            val_data (Optional[Dataset]): Validation data.
            training_args (TrainingArguments): Training configuration.
        """
        try:
            self.model = self.model.to(self.device)
            self.model = prepare_model(self.model)
            self.model = get_peft_model(self.model, LORA_CONFIG)
            trainer = Trainer(
                model=self.model,
                train_dataset=train_data,
                args=training_args,
                data_collator=DataCollatorForSeq2Seq(
                    self.tokenizer,
                    pad_to_multiple_of=8,
                    return_tensors="pt",
                    padding=True,
                ),
            )
            self.model.config.use_cache = False
            trainer.train()
            self.model.save_pretrained(self.model_path)
        except Exception as e:
            logging.error(f"Error in model training: {e}")

    def finetune(self, data_path, training_args):
        """
        Execute the fine-tuning pipeline.

        Parameters:
            data_path (str): Path to the data for fine-tuning.
            training_args (TrainingArguments): Training configuration.
        """
        try:
            df = pd.read_csv(data_path)
            df = df.drop('Unnamed: 0', axis=1)
            # To reset the indices
            dataset = Dataset(pa.Table.from_pandas(df))
            train_data = load_dataset(data_path)
            self.train_model(train_data, training_args)
        except KeyboardInterrupt:
            print("Interrupt received, saving model...")
            self.model.save_pretrained(f"{self.model_path}_interrupted")
            print(f"Model saved to {self.model_path}_interrupted")
        except Exception as e:
            logging.error(f"Error in fintuning: {e}")

ENABLE_WANDB = False

def lets_finetune(
    device=DEVICE,
    model=BASE_MODEL,
    per_device_batch_size=4,
    warmup_steps=5,
    learning_rate=2e-5,
    max_steps=10,
    gradient_accum_steps=4,
):
    try:
        # Training parameters
        save_steps = 5
        eval_steps = 5
        max_grad_norm = 0.3
        save_total_limit = 3
        logging_steps = 5

        print("\n" + "\033[1;34m" + "=" * 60 + "\033[0m")
        print("\033[1;34mTraining Parameters:\033[0m")
        param_format = "\033[1;34m{:<25} {}\033[0m"
        print(param_format.format("Foundation model:", BASE_MODEL))
        print(param_format.format("Model save path:", MODEL_PATH))
        print(param_format.format("Device used:", DEVICE))
        if DEVICE.type.startswith("xpu"):
            print(param_format.format("Intel GPU:", torch.xpu.get_device_name()))
        print(param_format.format("Batch size per device:", per_device_batch_size))
        print(param_format.format("Gradient accum. steps:", gradient_accum_steps))
        print(param_format.format("Warmup steps:", warmup_steps))
        print(param_format.format("Save steps:", save_steps))
        print(param_format.format("Evaluation steps:", eval_steps))
        print(param_format.format("Max steps:", max_steps))
        print(param_format.format("Learning rate:", learning_rate))
        print(param_format.format("Max gradient norm:", max_grad_norm))
        print(param_format.format("Save total limit:", save_total_limit))
        print(param_format.format("Logging steps:", logging_steps))
        print("\033[1;34m" + "=" * 60 + "\033[0m\n")

        # Initialize the finetuner with the model and device information
        finetuner = FineTuner(
            base_model_id=model, model_path=MODEL_PATH, device=device
        )

        training_args = TrainingArguments(
            per_device_train_batch_size=per_device_batch_size,
            gradient_accumulation_steps=gradient_accum_steps,
            warmup_steps=warmup_steps,
            save_steps=save_steps,
            save_strategy="steps",
            eval_steps=eval_steps,
            evaluation_strategy="steps",
            max_steps=max_steps,
            learning_rate=learning_rate,
            #max_grad_norm=max_grad_norm,
            bf16=True,
            #lr_scheduler_type="cosine",
            load_best_model_at_end=True,
            ddp_find_unused_parameters=False,
            group_by_length=True,
            save_total_limit=save_total_limit,
            logging_steps=logging_steps,
            optim="adamw_hf",
            output_dir="./lora_adapters",
            logging_dir="./logs",
            report_to="wandb" if ENABLE_WANDB else [],
        )

        # Start fine-tuning
        finetuner.finetune(DATA_PATH, training_args)
    except Exception as e:
        logging.error(f"Error occurred: {e}")

lets_finetune()



