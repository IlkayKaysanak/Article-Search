def map_emails_to_authors(authors, emails):
    email_author_map = {}
    
    for email in emails:
        for author in authors:
            author_name_parts = author.lower().split()
            if any(part in email.lower() for part in author_name_parts):
                email_author_map[email] = author
                break
    
    return email_author_map