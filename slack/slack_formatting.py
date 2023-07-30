import re

def convert_markdown_to_slack(markdown_text):
    bold_dict = {}  # Dictionary to store converted bold text

    # Find all occurrences of Bolt's double asterisk-wrapped text (bold)
    matches = re.findall(r'\*\*(.*?)\*\*', markdown_text)

    # Replace each match with a unique key and store the converted text in the dictionary
    for i, match in enumerate(matches):
        unique_key = f'__BOLD_{i}__'
        bold_dict[unique_key] = f'*{match}*'
        markdown_text = markdown_text.replace(f'**{match}**', unique_key)

    # Find all occurrences of Bolt's single asterisk-wrapped text (italic)
    matches = re.findall(r'(?<!\*)\*(.*?)(?<!\*)\*', markdown_text)

    # Replace each match with a unique key and store the converted text in the dictionary
    for i, match in enumerate(matches):
        unique_key = f'__ITALIC_{i}__'
        bold_dict[unique_key] = f'*{match}*'
        markdown_text = markdown_text.replace(f'*{match}*', unique_key)

    # Find all occurrences of Bolt's strikethrough text
    matches = re.findall(r'~~(.*?)~~', markdown_text)

    # Replace each match with a unique key and store the converted text in the dictionary
    for i, match in enumerate(matches):
        unique_key = f'__STRIKE_{i}__'
        bold_dict[unique_key] = f'*{match}*'
        markdown_text = markdown_text.replace(f'~~{match}~~', unique_key)

    # Find all occurrences of Bolt's code blocks
    matches = re.findall(r'```(.+?)```', markdown_text, flags=re.DOTALL)

    # Replace each match with a unique key and store the converted text in the dictionary
    for i, match in enumerate(matches):
        unique_key = f'__CODE_{i}__'
        bold_dict[unique_key] = f'```{match}```'
        markdown_text = markdown_text.replace(f'```{match}```', unique_key)

    # Find all occurrences of Markdown unordered list items
    matches = re.findall(r'^\s*-\s+(.+)', markdown_text, flags=re.M)

    # Replace each match with Slack's bullet points markdown format
    for match in matches:
        slack_bullet_point = f'• {match}'  # Replace * with • (bullet point)
        markdown_text = markdown_text.replace(f'- {match}', slack_bullet_point)

    # Replace ordered list items with Slack's numbered list markdown format
    ordered_matches = re.findall(r'^\s*\d+\.\s+(.+)', markdown_text, flags=re.M)
    for match in ordered_matches:
        slack_ordered_point = f'{ordered_matches.index(match) + 1}. {match}'
        markdown_text = markdown_text.replace(f'{ordered_matches.index(match) + 1}. {match}', slack_ordered_point)

    # Restore original bold, italic, strikethrough, and code from the unique keys
    for key, value in bold_dict.items():
        markdown_text = markdown_text.replace(key, value)

    return markdown_text