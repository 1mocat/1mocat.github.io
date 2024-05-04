
import re

def split_and_save_html(file_path):
    # Read HTML content from the file
    with open(file_path, 'r') as file:
        content = file.read()

    # Split the HTML content based on '###'
    html_blocks = content.split('###')
    html_blocks = [block.strip() for block in html_blocks if block.strip()]

    # Regex to find title within the HTML
    title_pattern = re.compile(r'<title>(.*?)</title>')

    # Process each block of HTML
    for block in html_blocks:
        # Extract the title for use as the filename
        title_search = title_pattern.search(block)
        if title_search:
            title = title_search.group(1).strip()
            file_name = f'{title}.html'
            # Write the content to a file named after the title
            with open(file_name, 'w') as file:
                file.write(block)
            print(f'File saved: {file_name}')

# Path to the file containing HTML content
file_path = 'index3-More-generated-codes.html'

# Call the function with the path to the HTML file
split_and_save_html(file_path)