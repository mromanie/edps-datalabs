import ipywidgets as widgets
from IPython.display import display, clear_output
import requests
from bs4 import BeautifulSoup
import os


def decompress_files(directory):
    # Iterate over all files in the given directory
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        
        # Decompress .gz and .Z files using gunzip
        if filename.endswith('.gz') or filename.endswith('.Z'):
            os.system(f'gunzip "{file_path}"')


def safe_extract_filter(member, tar):
    # Prevent path traversal attacks
    target_path = os.path.abspath(os.path.join('.', member.name))
    if not target_path.startswith(os.path.abspath('.')):
        raise Exception("Attempted Path Traversal in Tar File")
    return member


def run_tap_query(tap, query):
    results = None

    # define a job that will run the query asynchronously 
    job = tap.submit_job(query)
    
    # extending the maximum duration of the job to 300s (default 60 seconds)
    job.execution_duration = 300 # max allowed: 3600s
    
    # job initially is in phase PENDING; you need to run it and wait for completion: 
    job.run()
    
    try:
        job.wait(phases=["COMPLETED", "ERROR", "ABORTED"], timeout=600.)
    except pyvo.DALServiceError:
        print('Exception on JOB {id}: {status}'.format(id=job.job_id, status=job.phase))
    
    print("Job: %s %s" %(job.job_id, job.phase))
    
    if job.phase == 'COMPLETED':
        # When the job has completed, the results can be fetched:
        results = job.fetch_result()
    
    # the job can be deleted (always a good practice to release the disk space on the ESO servers)
    job.delete()

    return results


class TextSelector:
    def __init__(self, default_description=None, default_input=None):
        self.text_input = widgets.Text(
            value=default_input,
            placeholder='Input',
            description=default_description,
            disabled=False
        )

        self.submit_button = widgets.Button(
            description='Select',
            layout=widgets.Layout(width='100px'),
            style=widgets.ButtonStyle(button_color='lightgreen')
        )

        self.output = widgets.Output()
        self.submit_button.on_click(self.on_submit_clicked)

        # This will store the selected inout
        self.selected_input = default_input

    def on_submit_clicked(self, b):
        with self.output:
            clear_output()
            self.selected_input = self.text_input.value
            print(f"OK, provided input is: {self.selected_input}")
            # You can trigger any follow-up action here

    def display(self):
        display(self.text_input, self.submit_button, self.output)

    def get_input(self):
        return self.selected_input


class URLExtractor:
    def __init__(self, html_url, instrument):
        self.instrument = instrument
        self.html_url = html_url
        self.soup = self._load_html()

    def _load_html(self):
        # Fetch the HTML content from the URL
        response = requests.get(self.html_url)
        html_content = response.content
        return BeautifulSoup(html_content, 'html.parser')
        
    def _load_html(self):
        # with open(self.html_url, 'r', encoding='utf-8') as file:
            # html_content = file.read()
        # Fetch the HTML content from the URL
        response = requests.get(self.html_url)
        html_content = response.content
        return BeautifulSoup(html_content, 'html.parser')

    def extract_urls(self):
        pattern1 = 'https://ftp.eso.org/pub/dfs/pipelines/instruments/'
        pattern2 = self.instrument + '-demo-reflex'

        links = self.soup.find_all('a', href=True)
        for link in links:
            href = link['href']
            if pattern2 in href and pattern2 in href:
                return link['href']

        return None
    

class DemoDataExtractor:
    def __init__(self, html_url):
        self.html_url = html_url
        self.soup = self._load_html()

    def _load_html(self):
        # with open(self.html_url, 'r', encoding='utf-8') as file:
            # html_content = file.read()
        # Fetch the HTML content from the URL
        response = requests.get(self.html_url)
        html_content = response.content
        return BeautifulSoup(html_content, 'html.parser')

    def _find_instrument_row(self, instrument_name):
        # Find the correct table by checking for the 'Instrument' header
        for table in self.soup.find_all('table'):
            if 'Instrument' in table.text:
                for row in table.find_all('tr'):
                    first_td = row.find('td')
                    if first_td and instrument_name.lower() in first_td.text.lower():
                        return row
        return None

    def get_demo_data_link(self, instrument_name):
        instrument_row = self._find_instrument_row(instrument_name)
        if not instrument_row:
            return None

        hrefs = [a['href'] for a in instrument_row.find_all('a', href=True)]
        demo_data_href = next((href for href in hrefs if 'demo-reflex' in href), None)
        return demo_data_href
