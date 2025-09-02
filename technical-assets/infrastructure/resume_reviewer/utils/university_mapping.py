import re
from typing import Dict, List, Tuple

# Mapping of email domains to university names
UNIVERSITY_MAPPING = {
    'csub.edu': 'California State University, Bakersfield',
    'caub.edu': 'California State University, Bakersfield',
    'csuci.edu': 'California State University Channel Islands',
    'myci.csuci.edu': 'California State University Channel Islands',
    'csuchico.edu': 'California State University, Chico',
    'csudh.edu': 'California State University, Dominguez Hills',
    'toromail.csudh.edu': 'California State University, Dominguez Hills',
    'csueastbay.edu': 'California State University, East Bay',
    'fresnostate.edu': 'California State University, Fresno',
    'mail.fresnostate.edu': 'California State University, Fresno',
    'mail.fresnostate.com': 'California State University, Fresno',
    'fresno.state.edu': 'California State University, Fresno',
    'mail.fresno.state.edu': 'California State University, Fresno',
    'csu.fullerton.edu': 'California State University, Fullerton',
    'humboldt.edu': 'California State Polytechnic University, Humboldt',
    'student.csulb.edu': 'California State University, Long Beach',
    'csulb.edu': 'California State University, Long Beach',
    'calstatela.edu': 'California State University, Los Angeles',
    'csum.edu': 'California State University Maritime Academy',
    'csumb.edu': 'California State University, Monterey Bay',
    'my.csun.edu': 'California State University, Northridge',
    'csun.edu': 'California State University, Northridge',
    'cpp.edu': 'California State Polytechnic University, Pomona',
    'hornet.csus.edu': 'California State University, Sacramento',
    'csus.edu': 'California State University, Sacramento',
    'coyote.csusb.edu': 'California State University, San Bernardino',
    'csusb.edu': 'California State University, San Bernardino',
    'sdsu.edu': 'San Diego State University',
    'mail.sfsu.edu': 'San Francisco State University',
    'sfsu.edu': 'San Francisco State University',
    'sjsu.edu': 'San José State University',
    'calpoly.edu': 'California Polytechnic State University, San Luis Obispo',
    'csusm.edu': 'California State University San Marcos',
    'sonoma.edu': 'Sonoma State University',
    'csustan.edu': 'California State University, Stanislaus'
}

def extract_domain(email: str) -> str:
    """Extract domain from email address."""
    if not email or '@' not in email:
        return ''
    return email.split('@')[-1].lower()

def get_university_name(email: str) -> str:
    """Get university name from email address."""
    domain = extract_domain(email)
    return UNIVERSITY_MAPPING.get(domain, 'Other')

def verify_university_mappings(emails: List[str]) -> Tuple[Dict[str, int], List[str]]:
    """
    Verify university mappings and return statistics.
    
    Args:
        emails: List of email addresses to verify
        
    Returns:
        Tuple containing:
        - Dictionary of university counts
        - List of unrecognized email examples
    """
    university_counts = {}
    unrecognized_emails = []
    
    for email in emails:
        university = get_university_name(email)
        university_counts[university] = university_counts.get(university, 0) + 1
        
        if university == 'Other':
            unrecognized_emails.append(email)
    
    return university_counts, unrecognized_emails

def print_verification_stats(university_counts: Dict[str, int], unrecognized_emails: List[str], total_emails: int):
    """Print verification statistics."""
    print("\nUniversity Distribution:")
    print("-" * 50)
    for university, count in sorted(university_counts.items()):
        percentage = (count / total_emails) * 100
        print(f"{university}: {count} ({percentage:.1f}%)")
    
    print("\nUnrecognized Emails (up to 10 examples):")
    print("-" * 50)
    for email in unrecognized_emails[:10]:
        print(email)
    
    unrecognized_percentage = (len(unrecognized_emails) / total_emails) * 100
    print(f"\nTotal unrecognized emails: {len(unrecognized_emails)} ({unrecognized_percentage:.1f}%)") 