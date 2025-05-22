# Spill3r

**Spill3r** is a fast, pluggable Python tool for scanning S3 buckets for public misconfigurations. It is intended for **educational, auditing, and internal assessment** purposes only.

> 🛑 **Disclaimer**: This tool is provided for lawful security testing, red teaming, and educational purposes. The authors of this tool are not responsible for any misuse. Ensure you have **explicit permission** before scanning any infrastructure or cloud assets you do not own.

---

## ✨ Features

- Detect publicly **listable** S3 buckets  
- Test for **writeable** access (with optional test file deletion)  
- Supports **dry-run** mode for safe scanning  
- Multi-threaded scanning with a wordlist  
- JSON **logging** of results for automation and audits  
- Pretty CLI output with [`rich`](https://github.com/Textualize/rich) (optional)  

---

## 🚀 Usage

### 📚 Wordlists

Copy `sample-wordlist.txt` and add your own bucket names to the `wordlists/` folder.

#### 🔹 Format

A simple list of bucket names, one per line:

```text
company-logs
cdn-assets
staging-bucket
public-reports
```

### 🔹 Scan a single bucket
```bash
poetry run spill3r --bucket my-bucket-name
```
### 🔹 Scan with a wordlist (Threads optional)
```bash
poetry run spill3r --wordlist wordlists/common-buckets.txt --threads 10
```
### 🔹 Enable write test and cleanup
```bash
poetry run spill3r --wordlist wordlists/common-buckets.txt --write-check --cleanup
```
### 🔹 Dry run (simulate write check without uploading)
```bash
poetry run spill3r --wordlist wordlists/common-buckets.txt --write-check --dry-run
```
### 🔹 Output results to JSON
```bash
poetry run spill3r --wordlist wordlists/common-buckets.txt --output results.json
```
### 🔹 Run Tests
```bash
poetry run pytest tests/
```
### 🧰 Installation
	1.Install Poetry
	2.Clone this repo:
```bash
          git clone https://github.com/yourname/spill3r.git
          cd spill3r
          poetry install
```
### 🛡️ Legal Use & Ethics

- Spill3r is a security research tool. It should only be used:
    - infrastructure you own
	- With permission from the asset owner
	- As part of authorized security assessments

- Misuse may be illegal and unethical. Always follow your local laws, regulations, and best practices.

🔗 **Author:** [Raydar (Jarrad Pemberton)](https://github.com/jarrad411)

### 📝 License

MIT License — See [LICENSE](https://opensource.org/license/mit)