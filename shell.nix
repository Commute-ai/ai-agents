{
  pkgs ? import <nixpkgs> { },
}:

pkgs.mkShell {
  buildInputs = with pkgs; [
    python311
    uv
    gnumake
  ];

  # Set up environment variables
  shellHook = ''
    export UV_PYTHON=$(which python)
    export PYTHONPATH="$(pwd)/src:$PYTHONPATH"
    export UV_CACHE_DIR="$HOME/.cache/uv"
    mkdir -p "$UV_CACHE_DIR"

    if [[ -f "uv.lock" ]]; then
      uv sync --python "$UV_PYTHON"
      if [[ -d ".venv" ]]; then
        source .venv/bin/activate
      fi
    fi
  '';

  # Prevent nixpkgs Python packages from interfering
  NIX_ENFORCE_PURITY = 0;

  # Help uv find the right Python
  UV_PYTHON_PREFERENCE = "system";
}
