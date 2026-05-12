Installation & Setup
1. Prerequisites
Ensure you have the following installed on your system:

Python 3.10+

MySQL Server

MySQL Workbench (for database management)

2. Virtual Environment Setup
It is highly recommended to run this project inside a virtual environment to avoid library conflicts.

Bash
# Create the environment
python -m venv .venv

# Activate the environment (Windows)
.venv\Scripts\activate

# Activate the environment (Mac/Linux)
source .venv/bin/activate
3. Install Required Libraries
Install all dependencies using the following command:

Bash
pip install playwright fastapi uvicorn mysql-connector-python pandas scikit-learn streamlit apscheduler plotly python-dotenv
4. Playwright Browser Setup
Playwright requires its own browser binaries to run:

Bash
playwright install chromium