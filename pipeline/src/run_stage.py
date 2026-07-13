#!/usr/bin/env python3
"""
run_stage.py
============
Runner script untuk menjalankan pipeline stage berdasarkan parameter --stage.
Dirancang untuk dipanggil dari n8n dengan parameter --stage dan --url.

Usage:
    python3 run_stage.py --stage 1_download --url "https://www.youtube.com/watch?v=..."
    python3 run_stage.py --stage 2_transcribe --url "https://www.youtube.com/watch?v=..."
    python3 run_stage.py --stage 3_director_analysis --url "https://www.youtube.com/watch?v=..."
    python3 run_stage.py --stage 4_cut_video --url "https://www.youtube.com/watch?v=..."
    python3 run_stage.py --stage 5_add_caption --url "https://www.youtube.com/watch?v=..."

Example from N8N:
    python3 run_stage.py --stage 2_transcribe --url "https://www.youtube.com/watch?v=k2PfoSoofEo&t=4056s"

Output:
    JSON response dengan status "success" atau "error"
    Exit code 0 untuk success, 1 untuk error
"""

import argparse
import json
import sys
import config
from checkpoint_manager import CheckpointManager

# Import stage modules
from download_file import do_download
from transcribe_supadata import transcribe_supadata
from director import director
from cut_video import cut_video
from add_caption import add_caption

# Map stage names to their functions
STAGE_MAPPING = {
    config.STAGE_DOWNLOAD: {
        "function": do_download,
        "name": "Download Video"
    },
    config.STAGE_TRANSCRIBE: {
        "function": transcribe_supadata,
        "name": "Transcribe Video"
    },
    config.STAGE_DIRECTOR_ANALYSIS: {
        "function": director,
        "name": "Director Analysis"
    },
    config.STAGE_CUT_VIDEO: {
        "function": cut_video,
        "name": "Cut Video"
    },
    config.STAGE_ADD_CAPTION: {
        "function": add_caption,
        "name": "Add Caption"
    }
}


def run_stage(stage_name, url=None, continue_step=False):
    """
    Menjalankan stage pipeline yang diminta
    
    Args:
        stage_name: Nama stage (e.g., "1_download", "2_transcribe")
        url: YouTube URL (diperlukan untuk beberapa stage)
        continue_step: Boolean, apakah akan melanjutkan dari state terakhir.
        
    Returns:
        dict: Response dengan status dan data hasil
    """
    
    # Validasi stage name
    if stage_name not in STAGE_MAPPING:
        raise ValueError(
            f"Stage '{stage_name}' tidak dikenali. "
            f"Available stages: {', '.join(STAGE_MAPPING.keys())}"
        )
    
    stage_config = STAGE_MAPPING[stage_name]
    stage_display_name = stage_config["name"]
    
    # Validasi URL jika stage download
    if stage_name == config.STAGE_DOWNLOAD and not url:
        raise ValueError(
            f"Stage '{stage_name}' ({stage_display_name}) memerlukan parameter --url"
        )

    # Initialize CheckpointManager
    cm = CheckpointManager()

    # Tentukan list stage yang akan dijalankan
    if continue_step:
        try:
            start_idx = config.STAGES.index(stage_name)
            stages_to_run = config.STAGES[start_idx:]
        except ValueError:
            stages_to_run = [stage_name]
    else:
        stages_to_run = [stage_name]
        
    # Jalankan stage dengan error handling
    try:
        # Reset target stages ke pending agar mereka benar-benar dijalankan (tidak di-skip)
        current_state = cm.get_state()
        if current_state:
            for s in stages_to_run:
                cm.update_stage(s, "pending")
        
        results = {}
        for s_name in stages_to_run:
            s_config = STAGE_MAPPING[s_name]
            s_func = s_config["function"]
            
            print(f"🔄 Executing stage in sequence: {s_name}", file=sys.stderr)
            
            # Untuk stage download, panggil function langsung dengan url
            if s_name == config.STAGE_DOWNLOAD:
                result = cm.run_stage(s_name, lambda: s_func(url, config.TEMP_DIR))
            else:
                result = cm.run_stage(s_name, s_func)
            
            results[s_name] = result
        
        # Cek apakah semua stage dalam config.STAGES telah completed
        final_state = cm.get_state()
        if final_state:
            all_completed = True
            for s in config.STAGES:
                if final_state.get("stages", {}).get(s, {}).get("status") != "completed":
                    all_completed = False
                    break
            if all_completed:
                final_state["global_status"] = "completed"
                cm._write_data(final_state)
        
        return {
            "status": "success",
            "stage": stage_name,
            "stage_name": stage_display_name,
            "result": results.get(stage_name, True),
            "all_results": results
        }
        
    except Exception as e:
        raise Exception(f"Error menjalankan sequence stage dimulai dari '{stage_display_name}': {str(e)}")


def main():
    """Main entry point untuk script"""
    parser = argparse.ArgumentParser(
        description="Menjalankan pipeline stage berdasarkan parameter --stage"
    )
    parser.add_argument(
        "--stage",
        type=str,
        required=True,
        help=f"Stage yang akan dijalankan. Options: {', '.join(STAGE_MAPPING.keys())}"
    )
    parser.add_argument(
        "--url",
        type=str,
        required=False,
        help="YouTube URL (diperlukan untuk stage download)"
    )
    parser.add_argument(
        "--continue-step",
        action="store_true", # This will make it a boolean flag
        required=False,
        help="Melanjutkan eksekusi dari stage terakhir yang gagal atau belum selesai."
    )
    
    args = parser.parse_args()
    
    try:
        result = run_stage(args.stage, args.url, args.continue_step)
        
        # Output JSON response
        print(json.dumps(result, indent=2))
        
        # Exit dengan code 0 untuk success
        sys.exit(0)
        
    except ValueError as e:
        # Validation error
        error_response = {
            "status": "error",
            "error": str(e),
            "error_type": "validation_error"
        }
        print(json.dumps(error_response, indent=2), file=sys.stderr)
        sys.exit(1)
        
    except Exception as e:
        # General error
        error_response = {
            "status": "error",
            "error": str(e),
            "error_type": "execution_error"
        }
        print(json.dumps(error_response, indent=2), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()