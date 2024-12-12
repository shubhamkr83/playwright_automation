# Thriwe Automation Testing
PYTHON - PLAYRIGHT (HEADLESS)

Here's a step-by-step guide to setting up a Python Playwright project from GitHub, installing dependencies, and running the test script:

### **1. Install Python**
1. Download Python:
   - Visit the official [Python website](https://www.python.org/downloads/).
   - Download the latest stable version of Python for your operating system.
2. Install Python:
   - Run the downloaded installer.
   - **Important**: During installation, check the box that says **"Add Python to PATH"**.
3. Verify the installation:
   - Open a terminal or command prompt.
   - Run:
     ```bash
     python --version
     ```
     or
     ```bash
     python3 --version
     ```
   - You should see the installed version of Python.

---

### **2. Clone the GitHub Repository**
1. Open your terminal or command prompt.
2. Navigate to the directory where you want to clone the project.
   ```bash
   cd /path/to/your/directory
   ```
3. Clone the repository:
   ```bash
   git clone <repository_url>
   ```
   Replace `<repository_url>` with the actual URL of the GitHub repository.

---

### **3. Navigate to the Project Directory**
Change to the project directory:
```bash
cd /path/to/cloned-repository
```

---

### **4. Set Up a Virtual Environment (Optional but Recommended)**
1. Create a virtual environment:
   ```bash
   python -m venv venv
   ```
2. Activate the virtual environment:
   - **On Windows**:
     ```bash
     venv\Scripts\activate
     ```
   - **On macOS/Linux**:
     ```bash
     source venv/bin/activate
     ```

---

### **5. Install Dependencies**
1. Upgrade pip (optional but recommended):
   ```bash
   pip install --upgrade pip
   ```
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

---

### **6. Install Playwright Browsers**
Playwright requires downloading browser binaries. Run the following command to install them:
```bash
playwright install
```

---

### **7. Run the Test Script**
1. Identify the test script to be executed (e.g., `tests/test_login.py` or similar).
2. Run the script using `pytest` or directly with Python:
   - Using `pytest`:
     ```bash
     pytest main.py
     ```
   - Directly with Python:
     ```bash
     python main.py
     ```


