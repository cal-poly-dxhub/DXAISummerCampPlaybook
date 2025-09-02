# CSU AI Summer Camp - Candidate Selection Tool

This Streamlit application helps in selecting candidates for the CSU AI Summer Camp, ensuring a balanced distribution across universities and maintaining the desired technical/non-technical ratio.

## Features

- View and filter candidates by university, major type, and scores
- See detailed review information including individual reviewer scores and notes
- Track selection progress towards goals:
  - 2 candidates per university
  - 70% technical, 30% non-technical ratio
  - 100 total candidates
  - 50 waitlist candidates
- Manage selected candidates and waitlist
- View university distribution and selection metrics

## Setup

1. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the application:
   ```bash
   streamlit run app.py
   ```

## Usage

1. Use the sidebar filters to narrow down candidates:
   - Filter by university
   - Filter by major type (Technical/Non-Technical)
   - Set minimum score threshold
   - Sort by different criteria

2. For each candidate:
   - View basic information and average scores
   - Click "Toggle Details" to see individual reviewer scores and notes
   - Use "Approve" or "Waitlist" buttons to select candidates
   - View resume by clicking "View Resume"

3. Monitor progress:
   - Track number of selected and waitlisted candidates
   - View technical vs non-technical ratio
   - See university distribution

4. Manage selections:
   - View and manage selected candidates
   - View and manage waitlist
   - Remove candidates from either list if needed

## Data Structure

The application uses the following data sources:
- Candidate information from `rows/*/general.json` and `rows/*/metadata.json`
- Review scores from `test_reviews/*.json`
- AI scores from `resume_scores_final.csv` 