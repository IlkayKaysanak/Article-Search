def map_emails_to_authors(authors, emails):
    for author in authors:
        author_name_parts = re.split(r'\s+', author.name.lower())  
        for email in emails:
            email_lower = email.lower()
            if any(part in email_lower for part in author_name_parts):
                author.mail = email
                break  
    return authors