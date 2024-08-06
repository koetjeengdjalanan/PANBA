# PANBA

PANBA (Palo Alto Network Bulk Automation) is a tool designed for automating tasks related to Palo Alto Networks devices. It was developed by NTT Indonesia to streamline network management processes.

## Features

- **Automation Scripts**: Includes various scripts for automating network tasks.
- **Data Processing**: Utilizes Pandas for data manipulation and processing.
- **Compilation**: Uses Nuitka for compiling Python scripts into standalone executables.

## Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/koetjeengdjalanan/PANBA.git
   cd PANBA
   ```

2. **Set Up Virtual Environment**:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. **Running Scripts**:
   - To run a specific script, activate the virtual environment and execute the script using Python.

2. **Compilation**:
   - The project can be compiled into a standalone executable using the `compile.bat` script. This utilizes Nuitka to create a single file executable.

## Contributing

Contributions are welcome! Please fork the repository and create a pull request with your changes.

## License

This project is licensed under the **GNU Lesser General Public License (LGPL) v3.0**. You may obtain a copy of the License at [https://www.gnu.org/licenses/lgpl-3.0.html](https://www.gnu.org/licenses/lgpl-3.0.html).
