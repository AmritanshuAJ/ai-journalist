# AI Journalist

[](https://opensource.org/licenses/MIT)
[](https://www.python.org/downloads/)
[](https://fastapi.tiangolo.com/)
[](https://streamlit.io/)

AI Journalist creates personalized, daily audio news briefings based on your specified topics, keywords, and sources. It scrapes the latest news and discussions from the web, summarizes them using Google's Gemini LLM, and delivers a convenient, ready-to-listen audio report.

## 🌟 Features

  * **Personalized Content**: Generates news reports tailored to user-defined keywords and sources.
  * **Multi-Source Aggregation**: Scrapes content from major platforms like Google News and Reddit.
  * **AI-Powered Summarization**: Leverages Google's Gemini via LangChain and LangGraph for concise and coherent summaries.
  * **High-Quality Audio**: Converts the final news report into natural-sounding speech using ElevenLabs.
  * **Web-Based Interface**: Simple and interactive UI built with Streamlit.
  * **Robust Architecture**: Asynchronous backend powered by FastAPI for efficient request handling.
  * **Scalable Scraping**: Utilizes Bright Data for reliable and robust web scraping.

## ⚙️ Technical Architecture

The application follows a modern, decoupled architecture to ensure scalability and maintainability.

The workflow is as follows:

1.  **Frontend (Streamlit)**: The user inputs their topics of interest, keywords, and preferred sources (e.g., Google News, specific subreddits).
2.  **Backend (FastAPI)**: The frontend sends this payload to the FastAPI backend.
3.  **Scraping**: The backend triggers scraping modules that use **Bright Data** to fetch relevant articles from Google News and posts from Reddit. **NewsAPI** is used as a fallback in case of unavailability of **Bright Data** web browser scraping for Google News.
4.  **Content Processing**: The scraped text data undergoes a cleaning process.
5.  **Summarization (LLM)**: The cleaned content is passed to a processing pipeline built with **LangChain** and **LangGraph**. **Google Gemini** is used as the core Large Language Model to summarize the information into a cohesive news script.
6.  **Text-to-Audio Conversion**: The final script is sent to the **ElevenLabs** API to be converted into a high-quality audio file. **gTTS** is used as a fallback in case **ElevenLabs** credits are expired.
7.  **Output**: The generated audio report is delivered back to the user on the Streamlit interface for listening.

## 📂 Project Structure

The repository is organized to separate concerns between the frontend, backend, scraping logic, and utilities.

```
AI-JOURNALIST/
├── audio/                 # Directory for storing generated audio files
├── .env                   # Environment variables (API keys, etc.)
├── .gitignore             # Git ignore file
├── backend.py             # FastAPI application logic
├── check_env.py           # Utility to check for environment variables
├── debug_data.py          # Script for debugging data flow
├── free_news_scraper.py   # Scraper for sources without authentication
├── frontend.py            # Streamlit frontend application
├── models.py              # Pydantic models for data validation
├── news_scraper.py        # Google News scraper module
├── Pipfile                # Pipenv dependencies
├── Pipfile.lock           # Pipenv lock file
├── README.md              # This file
├── reddit_scraper.py      # Reddit scraper module
└── utils.py               # Utility functions
```

## 🚀 Getting Started

Follow these instructions to get a local copy up and running.

### Prerequisites

  * Python 3.9+
  * [Pipenv](https://www.google.com/search?q=https://pipenv.pypa.io/en/latest/installation/) for package management.

### Installation

1.  **Clone the repository:**

    ```sh
    git clone https://github.com/your-username/ai-journalist.git
    cd ai-journalist
    ```

2.  **Set up environment variables:**
    Create a `.env` file in the root directory by copying the example file (you may need to create `.env.example` first).

    ```sh
    cp .env.example .env
    ```

    Populate the `.env` file with your API keys:

    ```ini
    # Google API Key for Gemini
    GEMINI_API_KEY="YOUR_GEMINI_API_KEY"

    # ElevenLabs API Key
    ELEVENLABS_API_KEY="YOUR_ELEVENLABS_API_KEY"

    # Bright Data API Credentials
    BRIGHTDATA_USERNAME="YOUR_BRIGHTDATA_USERNAME"
    BRIGHTDATA_PASSWORD="YOUR_BRIGHTDATA_PASSWORD"
    ```

3.  **Install dependencies:**
    Use Pipenv to install the required packages from the `Pipfile`.

    ```sh
    pipenv install
    ```

4.  **Activate the virtual environment:**

    ```sh
    pipenv shell
    ```

### Running the Application

You need to run the backend and frontend services in separate terminals.

1.  **Start the FastAPI Backend:**

    ```sh
    uvicorn backend:app --reload
    ```

    The backend will be available at `http://127.0.0.1:8000`.

2.  **Start the Streamlit Frontend:**

    ```sh
    streamlit run frontend.py
    ```

    The frontend will open in your browser, typically at `http://localhost:8501`.

## Usage

1.  Navigate to the Streamlit application URL in your browser.
2.  Enter the keywords or topics you are interested in.
3.  Select the sources you want to pull information from (e.g., Google News, Reddit).
4.  Click the "Generate News Report" button.
5.  Wait for the system to scrape, process, and generate the summary.
6.  Once ready, an audio player will appear, allowing you to listen to your personalized news report.

## 🤝 Contributing

Contributions are what make the open-source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

1.  Fork the Project
2.  Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3.  Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4.  Push to the Branch (`git push origin feature/AmazingFeature`)
5.  Open a Pull Request

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

## 🙏 Acknowledgments

  * [Streamlit](https://streamlit.io/)
  * [FastAPI](https://fastapi.tiangolo.com/)
  * [Google Gemini](https://deepmind.google/technologies/gemini/)
  * [ElevenLabs](https://elevenlabs.io/)
  * [LangChain](https://www.langchain.com/)
  * [Bright Data](https://brightdata.com/)
