import os
import unittest
import json
from flask_sqlalchemy import SQLAlchemy

from flaskr import create_app
from models import setup_db


class TriviaTestCase(unittest.TestCase):
    """This class represents the trivia test case"""

    def setUp(self):
        """Define test variables and initialize app."""
        self.CATEGORIES = set(['Science', 'Art', 'Geography', 'History', 'Entertainment', 'Sports'])
        self.app = create_app()
        self.client = self.app.test_client
        self.database_name = "trivia"
        self.database_path = 'postgresql://jogallar@{}/{}'.format('localhost:5432', self.database_name)
        setup_db(self.app, self.database_path)

        # binds the app to the current context
        with self.app.app_context():
            self.db = SQLAlchemy()
            self.db.init_app(self.app)
            # create all tables
            self.db.create_all()
    
    def tearDown(self):
        """Executed after reach test"""
        pass

    def test_get_categories_and_get_questions_by_category(self):
        # test categories
        res = self.client().get("/categories")
        dataCategories = json.loads(res.data)
        categories = set([dataCategories["categories"][key] for key in dataCategories["categories"]])

        self.assertEqual(res.status_code, 200)
        self.assertEqual(dataCategories["success"], True)
        self.assertEqual(len(dataCategories["categories"]), 6)
        self.assertEqual(categories, self.CATEGORIES)

        # test questions by category
        questionsPerCategory = {
            'Science': 3,
            'Art': 4,
            'Geography': 3,
            'History': 4,
            'Entertainment': 3,
            'Sports': 2,
        }
        maxID = None
        for category in dataCategories["categories"]:
            maxID = int(category) if maxID is None else max(maxID, int(category))
            res = self.client().get("/categories/{}/questions".format(category))
            data = json.loads(res.data)
            self.assertEqual(res.status_code, 200)
            self.assertEqual(data["success"], True)
            self.assertEqual(len(data["questions"]), questionsPerCategory[data["categories"][category]])

        nonExistentCategory = str(maxID + 1)
        res = self.client().get("/categories/{}/questions".format(nonExistentCategory))
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 404)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'resource not found')

    def test_get_questions(self):
        # test a valid request
        res = self.client().get("/questions")
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(len(data['questions']) > -1)
        self.assertTrue(data['total_questions'] > -1)
        self.assertEqual(len(data['current_category']), 6)
        self.assertEqual(set(data['current_category']), self.CATEGORIES)

    def test_get_questions_404_error(self):        
        # test an invalid page
        res = self.client().get("/questions")
        page = json.loads(res.data)['total_questions'] + 1
        res = self.client().get("/questions?page={}".format(page))
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 404)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'resource not found')

    def test_search_questions_ok_and_404(self):
        search = 'nAme'
        res = self.client().post('/questions', json = {'searchTerm': search})
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertEqual(len(data['questions']), 2)
        self.assertEqual(len(data['current_category']), 6)
        self.assertEqual(set(data['current_category']), self.CATEGORIES)

        expected_questions = [
            {
                'answer': 'Muhammad Ali',
                'category': 4,
                'difficulty': 1, 
                'question': "What boxer's original name is Cassius Clay?"
            },
            {
                'answer': 'Brazil',
                'category': 6,
                'difficulty': 3, 
                'question': 'Which is the only team to play in every soccer World Cup tournament?'
            }
        ]

        for (gotten, expected) in zip(data['questions'], expected_questions):
            self.assertEqual(gotten["answer"], expected["answer"])
            self.assertEqual(gotten["category"], expected["category"])
            self.assertEqual(gotten["difficulty"], expected["difficulty"])
            self.assertEqual(gotten["question"], expected["question"])
    
        search = 'asdfasdfsdf'
        res = self.client().post('/questions', json = {'searchTerm': search})
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 404)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'resource not found')

    def test_create_and_delete_question(self):
        jsonPost = {
            "question": "Who is the greatest dinosaur of all time?",
            "answer": "Yoko",
            "difficulty": 1,
            "category": "4",
        }
        res = self.client().post('/questions', json = jsonPost)
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(data["id"])
        questionId = data["id"]

        res = self.client().delete('/questions/{}'.format(questionId))
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)

        res = self.client().delete('/questions/{}'.format(questionId))
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 404)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'resource not found')

    def test_400_error(self):
        jsonPost = {
            "question": "Who is the greatest dinosaur of all time?",
            "difficulty": 1,
            "category": "4",
        }
        res = self.client().post('/questions', json = jsonPost)
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'bad request')

    def test_405_error(self):
        res = self.client().patch('/questions')
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 405)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'],  'method not allowed')

    def test_sports_game(self):
        previous_questions = []
        for i in range(3):
            jsonData = {
                "previous_questions": previous_questions,
                "quiz_category": {"id": 6}
            }
            res = self.client().post('/quizzes', json = jsonData)
            data = json.loads(res.data)
            self.assertEqual(res.status_code, 200)
            self.assertEqual(data['success'], True)
            if i == 2:
                self.assertFalse("question" in data)
            else:
                self.assertTrue(data['question'])
                self.assertFalse(data['question']['id'] in previous_questions)
                previous_questions.append(data['question']['id'])

    def test_all_game(self):
        for _ in range(10):
            previous_questions = []
            categories = set()
            for _ in range(5):
                jsonData = {
                    "previous_questions": previous_questions,
                    "quiz_category": {"id": 0}
                }
                res = self.client().post('/quizzes', json = jsonData)
                data = json.loads(res.data)
                self.assertEqual(res.status_code, 200)
                self.assertEqual(data['success'], True)
                self.assertTrue(data['question'])
                self.assertFalse(data['question']['id'] in previous_questions)
                previous_questions.append(data['question']['id'])
                categories.add(data['question']['category'])
            self.assertTrue(len(categories) > 1)

    def test_quizzes_error(self):
        jsonData = {
            "previous_questions": [],
            "quiz_category": {"id": 10}
        }
        res = self.client().post('/quizzes', json = jsonData)
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'bad request')

# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()