"""
Llama.cpp Python Wrapper
Interfaccia Python per chiamare llama-cli e processare output
"""

import subprocess
import json
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
import re


class LlamaInference:
    """Wrapper per llama.cpp inference"""

    def __init__(
        self,
        model_path: str,
        llama_cli_path: str = "./build/bin/llama-cli",
        default_params: Optional[Dict[str, Any]] = None,
    ):
        self.model_path = Path(model_path)
        self.llama_cli_path = Path(llama_cli_path)

        if not self.model_path.exists():
            raise FileNotFoundError(f"Model not found: {self.model_path}")

        if not self.llama_cli_path.exists():
            raise FileNotFoundError(f"llama-cli not found: {self.llama_cli_path}")

        # Parametri di default ottimizzati per Raspberry Pi 4
        self.default_params = default_params or {
            "n_ctx": 1024,
            "n_threads": 4,
            "n_batch": 32,
            "temperature": 0.7,
            "top_p": 0.9,
            "repeat_penalty": 1.05,
            "n_predict": 256,
        }

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Genera una risposta usando llama.cpp

        Returns:
            {
                "output": str,
                "tokens_generated": int,
                "tokens_per_second": float,
                "time_elapsed": float,
                "prompt_tokens": int,
            }
        """
        # Merge parametri
        run_params = {**self.default_params, **(params or {})}

        # Costruisci il prompt completo
        full_prompt = self._build_prompt(prompt, system_prompt)

        # Costruisci comando
        cmd = [
            str(self.llama_cli_path),
            "-m", str(self.model_path),
            "-p", full_prompt,
            "-n", str(run_params["n_predict"]),
            "-c", str(run_params["n_ctx"]),
            "-t", str(run_params["n_threads"]),
            "-b", str(run_params["n_batch"]),
            "--temp", str(run_params["temperature"]),
            "--top-p", str(run_params["top_p"]),
            "--repeat-penalty", str(run_params["repeat_penalty"]),
            "--log-disable",  # Disabilita log per output pulito
        ]

        # Esegui
        start_time = time.time()

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,  # 60s timeout
            )

            elapsed = time.time() - start_time

            if result.returncode != 0:
                raise RuntimeError(f"llama-cli error: {result.stderr}")

            # Parse output
            output_text = self._parse_output(result.stdout, full_prompt)

            # Estrai statistiche dal stderr (llama.cpp stampa stats lì)
            stats = self._parse_stats(result.stderr)

            return {
                "output": output_text,
                "tokens_generated": stats.get("tokens_generated", 0),
                "tokens_per_second": stats.get("tokens_per_second", 0.0),
                "time_elapsed": elapsed,
                "prompt_tokens": stats.get("prompt_tokens", 0),
            }

        except subprocess.TimeoutExpired:
            raise RuntimeError("Generation timeout (60s)")

    def _build_prompt(self, user_prompt: str, system_prompt: Optional[str]) -> str:
        """Costruisce il prompt nel formato Gemma"""
        if system_prompt:
            # Formato Gemma con system
            return f"""<start_of_turn>system
{system_prompt}<end_of_turn>
<start_of_turn>user
{user_prompt}<end_of_turn>
<start_of_turn>model
"""
        else:
            # Solo user
            return f"""<start_of_turn>user
{user_prompt}<end_of_turn>
<start_of_turn>model
"""

    def _parse_output(self, raw_output: str, prompt: str) -> str:
        """Estrae solo il testo generato dal modello"""
        # Rimuovi il prompt dall'output
        output = raw_output

        # Rimuovi il prompt se presente
        if prompt in output:
            output = output.split(prompt, 1)[-1]

        # Rimuovi markers Gemma
        output = output.replace("<start_of_turn>", "")
        output = output.replace("<end_of_turn>", "")
        output = output.replace("<start_of_turn>model", "")

        # Trim
        output = output.strip()

        return output

    def _parse_stats(self, stderr: str) -> Dict[str, Any]:
        """Estrae statistiche dal stderr di llama.cpp"""
        stats = {}

        # Pattern comuni in llama.cpp output
        # llama_print_timings:        load time =   XXX ms
        # llama_print_timings:      sample time =   XXX ms /   XXX runs
        # llama_print_timings: prompt eval time =   XXX ms /   XXX tokens
        # llama_print_timings:        eval time =   XXX ms /   XXX runs (XXX tokens/s)

        # Tokens generati
        match = re.search(r"eval time.*?/\s*(\d+)\s+runs", stderr)
        if match:
            stats["tokens_generated"] = int(match.group(1))

        # Tokens/s
        match = re.search(r"\((\d+\.\d+)\s+tokens/s\)", stderr)
        if match:
            stats["tokens_per_second"] = float(match.group(1))

        # Prompt tokens
        match = re.search(r"prompt eval time.*?/\s*(\d+)\s+tokens", stderr)
        if match:
            stats["prompt_tokens"] = int(match.group(1))

        return stats

    def adjust_for_temperature(self, cpu_temp: float):
        """Aggiusta parametri in base a temperatura CPU (Energy-Aware)"""
        if cpu_temp > 75:
            # Throttling preventivo
            self.default_params["n_ctx"] = 512
            self.default_params["n_predict"] = 128
            print(f"⚠️  CPU temp {cpu_temp}°C - reduced context to 512")
        elif cpu_temp > 70:
            self.default_params["n_ctx"] = 768
            print(f"⚠️  CPU temp {cpu_temp}°C - reduced context to 768")
        else:
            # Normale
            self.default_params["n_ctx"] = 1024


if __name__ == "__main__":
    # Test
    import sys

    model = sys.argv[1] if len(sys.argv) > 1 else "artifacts/gemma3-1b-q4_0.gguf"

    llama = LlamaInference(
        model_path=f"../../{model}",
        llama_cli_path="../../build/bin/llama-cli"
    )

    system = """You are Antonio Gemma3 Evo Q4, an offline self-learning AI.
Detect user language (IT/EN) and respond in the same language.
Be concise and helpful."""

    result = llama.generate(
        prompt="Ciao! Come funziona la memoria evolutiva?",
        system_prompt=system,
    )

    print("Output:", result["output"])
    print(f"\nStats: {result['tokens_generated']} tokens @ {result['tokens_per_second']:.2f} t/s")
    print(f"Time: {result['time_elapsed']:.2f}s")
