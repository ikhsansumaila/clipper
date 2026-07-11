#!/usr/bin/env python3
"""
run.py
======
Wrapper script untuk mengeksekusi script pipeline dengan batasan 
virtual memory (ulimit -v) dan batas waktu (timeout).

Usage:
    python3 run.py <script_name> [--timeout SECONDS] [--memory KB]

Example (from n8n):
    docker exec clipper_pipeline python3 run.py director.py --timeout 600 --memory 3000000
"""

import argparse
import os
import resource
import subprocess
import sys

def limit_virtual_memory(max_virtual_memory_kb: int):
    """
    Membatasi virtual memory yang dapat digunakan oleh proses Python ini
    serta child process yang akan di-spawn nanti (karena diwariskan).
    """
    if max_virtual_memory_kb <= 0:
        return
        
    max_vm_bytes = max_virtual_memory_kb * 1024
    
    try:
        # RLIMIT_AS adalah parameter limit virtual memory
        soft, hard = resource.getrlimit(resource.RLIMIT_AS)
        # Jangan melampaui limit OS jika hard limit ada (selain -1)
        if hard != -1 and max_vm_bytes > hard:
            max_vm_bytes = hard
            
        resource.setrlimit(resource.RLIMIT_AS, (max_vm_bytes, max_vm_bytes))
        print(f"🔒 Virtual memory dibatasi hingga: {max_virtual_memory_kb:,} KB", file=sys.stderr)
    except Exception as e:
        print(f"⚠️ Peringatan: Gagal menyetel batasan memori. Error: {e}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="Wrapper executor dengan Timeout & Memory Limit")
    parser.add_argument("script", help="Nama script yang akan dijalankan (misal: director.py)")
    parser.add_argument("--timeout", type=int, default=int(os.getenv("DEFAULT_TIMEOUT_EXEC", 600)), help="Batas waktu eksekusi dalam detik (default: 600)")
    parser.add_argument("--memory", type=int, default=int(os.getenv("DEFAULT_VIRTUAL_MEMORY_LIMIT_EXEC", 3000000)), help="Batas virtual memory dalam KB (default: 3000000)")
    
    # Ambil sisa argumen yang mungkin akan di-pass ke script target
    # (contoh: python3 run.py check_url_exists.py --url "http...")
    args, unknown_args = parser.parse_known_args()
    
    # 1. Set Memory Limit
    limit_virtual_memory(args.memory)
    
    # 2. Siapkan command eksekusi
    # Jika script bukan path absolute, tambahkan './'
    script_path = args.script if args.script.startswith("/") else f"./{args.script}"
    
    # Command: python3 <script_path> <unknown_args>
    command = [sys.executable, script_path] + unknown_args
    
    script_base_name = os.path.basename(args.script)
    print(f"🚀 Menjalankan {script_base_name} (Timeout: {args.timeout}s)...", file=sys.stderr)
    
    try:
        # 3. Eksekusi Subprocess dengan Timeout
        # Tidak pakai text=True agar stdout/stderr stream mentah bisa dilewatkan kalau diperlukan,
        # tapi subprocess.run akan block sampai selesai. 
        # Membiarkan stdout/stderr ke None membuat output langsung keluar di layar (pass-through).
        result = subprocess.run(command, timeout=args.timeout)
        
        # Keluar dengan exit code yang sama dengan script target
        sys.exit(result.returncode)
        
    except subprocess.TimeoutExpired:
        print(f"\n❌ Proses menjalankan script {script_base_name} dihentikan paksa karena terlalu lama (Timeout > {args.timeout}s).", file=sys.stderr)
        # Berikan exit code 124 (kode standar Linux untuk command timeout)
        sys.exit(124)
    except KeyboardInterrupt:
        print("\n⚠️ Proses dihentikan secara manual (KeyboardInterrupt).", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Error sistem gagal menjalankan {script_base_name}: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()