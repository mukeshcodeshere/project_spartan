# Project Spartan

Step-by-step guide to setting up and running **Project Spartan**.

## 📦 Prerequisites

* [Anaconda](https://www.anaconda.com/products/distribution) installed on your system.

---

## 🚀 Getting Started

Follow these steps to set up the environment and run the application:

### 1. Download and Install Anaconda

Download the installer from the [official Anaconda website](https://www.anaconda.com/products/distribution) and install it following the instructions for your operating system.

---

### 2. Open Anaconda Prompt

After installation, open the **Anaconda Prompt** from your start menu (Windows) or terminal (macOS/Linux).

---

### 3. Create and Activate a New Environment

In the Anaconda Prompt, run the following commands:

```bash
conda create --name work python=3.10
conda activate work
```

> This creates and activates a new environment named `work`.

---

### 4. Install Project Dependencies

Make sure you're in the project directory, then install the required packages:

```bash
pip install -r requirements.txt
```

---

### 5. Run the Application

Once the environment is ready and dependencies are installed, run the application and enter your MV Username and Password:

```bash
python run_app.py
```

---

## ✅ Done!

The application should now be running. Follow any additional instructions displayed in the terminal if applicable.

---


