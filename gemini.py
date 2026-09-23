import csv
import sys
import os
import time
from google import genai
from google.genai import types #pip install google-genai
from openai import OpenAI


SYSTEM_PROMPT = "You are a customer support assistant."
MAX_OUTPUT_TOKENS = 2000
TEMPERATURE = 0.7
MODEL = "gemini-3.1-flash-lite"
#MODEL = "qwen/qwen3.6-plus:free" #"qwen/qwen3.6-plus-preview:free"
#MODEL = "Qwen/Qwen3.6-27B"#"qwen/qwen3.6-plus"

from datetime import datetime, timezone


def log_to_csv(
    system_prompt, max_tokens, user_prompt, response, response_token_count,
    governed_max_tokens=None, injected_system_prompt=None,
    prompt_tokens=None, total_tokens=None
):
    file_name  = "llm_logs.csv"
    file_exists = os.path.isfile(file_name)
    current_time = datetime.now(timezone.utc).isoformat()
    headers = ["timestamp", "system_prompt", "max_tokens",
               "user_prompt", "response", "response_token_count",
               "governed_max_tokens", "injected_system_prompt",
               "prompt_tokens", "total_tokens"]

    with open(file_name, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=headers)

        # Write header row if the file is being created for the first time
        if not file_exists:
            writer.writeheader()

        # Append the call log
        writer.writerow({
            "timestamp":              current_time,
            "system_prompt":          system_prompt,
            "max_tokens":             max_tokens,
            "user_prompt":            user_prompt,
            "response":               response,
            "response_token_count":   response_token_count,
            "governed_max_tokens":    governed_max_tokens or "not_governed",
            "injected_system_prompt": injected_system_prompt or "none",
            "prompt_tokens":          prompt_tokens or 0,
            "total_tokens":           total_tokens or 0,
        })

def main():
    if len(sys.argv) != 3:
        print("Usage: python gemini-single-shot.py <csv_file> <number_of_prompts>")
        print("Example: python gemini-single-shot.py prompts.csv 300")
        sys.exit(1)

    csv_file = sys.argv[1]

    try:
        number_of_prompts = int(sys.argv[2])
    except ValueError:
        print("Error: number_of_prompts must be an integer.")
        sys.exit(1)

    if number_of_prompts <= 0:
        print("Error: number_of_prompts must be greater than 0.")
        sys.exit(1)

    if not os.path.exists(csv_file):
        print(f"Error: CSV file not found: {csv_file}")
        sys.exit(1)

    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    

    


    prompts = []

    # Read prompts from CSV
    with open(csv_file, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)

        if "prompt" not in reader.fieldnames:
            print("Error: CSV must contain a 'prompt' column.")
            sys.exit(1)

        for row in reader:
            prompt = row["prompt"].strip()

            if prompt:
                prompts.append(prompt)

            if len(prompts) >= number_of_prompts:
                break

    if not prompts:
        print("No prompts found in CSV.")
        sys.exit(1)

    print(f"Loaded {len(prompts)} prompts.")
    print("Sending prompts to Gemini...")

    successful = 0
    failed = 0

    for i, prompt in enumerate(prompts, start=1):
        # Retry mechanism for 429 Rate Limits
        max_retries = 3
        response = None

        governed_max = None
        injected_sys = None
        for attempt in range(max_retries):
            try:
                _config = types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=TEMPERATURE,
                    max_output_tokens=MAX_OUTPUT_TOKENS,
                    automatic_function_calling=types.AutomaticFunctionCallingConfig(
                        disable=True
                    ),
                )
                response = client.models.generate_content(
                    model=MODEL,
                    contents=prompt,
                    config=_config,
                )
                # Read back injected values from config object after DoCoreAI modified it
                governed_max  = getattr(_config, 'max_output_tokens', None)
                injected_sys  = getattr(_config, 'system_instruction', None)
                print(f"📋 Full system_instruction: \"{injected_sys}\"")
                
               
                break  # Exit retry loop if request succeeds
            except Exception as e:
                # Catch rate limit / quota errors and wait before retrying
                if "429" in str(e) and attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 5
                    print(f"[{i}/{len(prompts)}] Rate limit hit (429). Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise e  # Pass standard errors to outer block

        if response is None:
            failed += 1
            continue

        try:
            output = response.text or ""
            usage  = response.usage_metadata
            token_count = usage.candidates_token_count if usage else 0

# ----------------------------------------------------
            # INTEGRATION HERE: Log the call details to llm_logs.csv
            # ----------------------------------------------------
            
            

            log_to_csv(
                system_prompt=SYSTEM_PROMPT,
                max_tokens=MAX_OUTPUT_TOKENS,
                user_prompt=prompt,
                response=output,
                response_token_count=token_count,
                governed_max_tokens=governed_max,
                injected_system_prompt=injected_sys,
                prompt_tokens=usage.prompt_token_count if usage else None,
                total_tokens=usage.total_token_count if usage else None,
            )
            successful += 1

            print(f"[{i}/{len(prompts)}] Success")
            print(f"Prompt: {prompt}")
            print(f"Response: {output}")
            print()
            print("── Token Counts ──────────────────────────────────────")
            print(f"  Prompt tokens (system + user combined) : {usage.prompt_token_count if usage else 'N/A'}")
            print(f"  Completion tokens                      : {usage.candidates_token_count if usage else 'N/A'}")
            
            print(f"  Total tokens                           : {usage.total_token_count if usage else 'N/A'}")

            print(f"  Max output tokens (limit set)          : {MAX_OUTPUT_TOKENS}")
            print(f"  Governed max tokens (DoCoreAI)         : {governed_max or 'N/A'}")
            
            print(f"  Injected system prompt                 : {str(injected_sys)[:80] if injected_sys else 'N/A'}")

            print("------------------------------------------------------")
            print("── Character Lengths ─────────────────────────────────")
            print(f"  System prompt chars : {len(SYSTEM_PROMPT)}")
            print(f"  User prompt chars   : {len(prompt)}")
            print(f"  Response chars      : {len(output)}")
            print("-" * 60)
            time.sleep(7)  # Reduced delay between calls

        except Exception as e:
            failed += 1
            err_str = str(e)
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                print(f"[{i}/{len(prompts)}] ⏸️ Daily quota reached — stopping.")
                break
            print(f"[{i}/{len(prompts)}] ERROR: {type(e).__name__}: {err_str[:120]}")

    print("\nTest completed.")
    print(f"Successful: {successful}")
    print(f"Failed:     {failed}")
    print(f"Total:      {len(prompts)}")


if __name__ == "__main__":
    main()