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
    echo "🚀 AI Agents development environment (NixOS + uv)"
    echo "Python: $(python --version)"
    echo "uv: $(uv --version)"
    echo ""

    # Ensure uv uses system Python (avoid dynamic linking issues)
    export UV_PYTHON=$(which python)

    # Set up Python path for better IDE integration
    export PYTHONPATH="$(pwd)/src:$PYTHONPATH"

    # Make sure uv cache directory exists and is writable
    export UV_CACHE_DIR="$HOME/.cache/uv"
    mkdir -p "$UV_CACHE_DIR"

    # Optional: Auto-sync dependencies if uv.lock exists
    if [[ -f "uv.lock" ]]; then
      echo "📦 Found uv.lock, syncing dependencies..."
      uv sync --python "$UV_PYTHON"
      
      # Activate the virtual environment
      if [[ -d ".venv" ]]; then
        source .venv/bin/activate
        echo "✅ Virtual environment activated"
        echo "Python location: $(which python)"
      fi
    else
      echo "ℹ️  No uv.lock found. Run 'uv init' or 'uv add <package>' to get started."
    fi

    echo ""
    echo "🔧 Available commands:"
    echo "  uv add <package>     - Add a dependency"
    echo "  uv run <command>     - Run command in uv environment"
    echo "  uv sync              - Sync dependencies"
    echo "  python run.py        - Start the FastAPI server"
    echo "  pytest               - Run tests"
    echo ""
  '';

  # Prevent nixpkgs Python packages from interfering
  NIX_ENFORCE_PURITY = 0;

  # Help uv find the right Python
  UV_PYTHON_PREFERENCE = "system";
}
