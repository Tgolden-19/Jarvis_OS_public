cd ~/JARVIS_BMOS

echo "entering virtual environment"
source .venv/bin/activate

echo "launching BMO program"
python3 main.py

echo "deactivating env"
deactivate