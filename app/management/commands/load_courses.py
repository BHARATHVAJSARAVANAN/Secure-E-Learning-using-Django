import csv
from django.core.management.base import BaseCommand
from app.models import LearningResource
import pandas as pd

class Command(BaseCommand):
    help = 'Load courses from a CSV file into the LearningResource model'
    
    @staticmethod
    def convert_to_int(value):
        if isinstance(value, str):
            value = value.lower().replace(',', '').strip()  # Remove commas and lowercase
            if not value:
                return 0  # Default value for empty strings
            if 'k' in value:
                return int(float(value.replace('k', '').strip()) * 1000)
            elif 'm' in value:
                return int(float(value.replace('m', '').strip()) * 1000000)
            else:
                try:
                    return int(value)
                except ValueError:
                    return 0  # Default value for invalid integers
        return 0  # Default value for non-string values

    
    

    def add_arguments(self, parser):
        # parser.add_argument('csv_file', type=str, help='The CSV file to load', default="coursera_courses.csv")
        parser.add_argument('--path', type=str, help='The CSV file to load', default="coursera_courses.csv", required=True)

    def handle(self, *args, **kwargs):
        csv_file = kwargs['path']

        with open(csv_file, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                
                course_reviews_num = row.get('course_reviews_num', '')
                course_reviews_num = self.convert_to_int(course_reviews_num)
                
                LearningResource.objects.create(
                    course_title=row.get('course_title', ''),
                    course_organization=row.get('course_organization', ''),
                    course_certificate_type=row.get('course_certificate_type', ''),
                    course_duration=row.get('course_duration', ''),  # Use .get() to avoid KeyError
                    course_rating=row.get('course_rating', ''),
                    course_reviews_num=course_reviews_num,
                   
                    course_difficulty=row.get('course_difficulty', ''),
                    course_url=row.get('course_url', ''),
                    course_students_enrolled=row.get('course_students_enrolled', ''),
                    course_skills=row.get('course_skills', ''),
                    course_summary=row.get('course_summary', ''),
                    course_description=row.get('course_description', ''),
                )
        self.stdout.write(self.style.SUCCESS('Courses loaded successfully.'))
        
    
