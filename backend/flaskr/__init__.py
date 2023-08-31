import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10
NO_QUESTIONS_TO_SHOW_MESSAGE = "No questions to show"
NO_CATEOGIRES_TO_SHOW_MESSAGE = "No categories to show"
NO_QUESTION_FOUND_MESSAGE = "No question found"
INVALID_CATEGORY = "Invalid category"

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)
    CORS(app, resources = {r"/*": {"origins": "*"}})

    # CORS Headers
    @app.after_request
    def after_request(response):
        response.headers.add(
            "Access-Control-Allow-Headers", "Content-Type,Authorization,true"
        )
        response.headers.add(
            "Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS"
        )
        return response

    @app.route("/categories")
    def get_categories():
        try:
            categories = [category.format() for category in Category.query.all()]
            if len(categories) == 0:
                raise Exception(NO_CATEOGIRES_TO_SHOW_MESSAGE)
            return jsonify({
                    "success": True,
                    "categories": {category["id"]: category["type"] for category in categories},
                })
        except Exception as e:
            if e.__str__() == NO_CATEOGIRES_TO_SHOW_MESSAGE:
                abort(404)
            else:
                abort(422)
    
    def paginate_questions(request, selection):
        page = request.args.get("page", 1, type = int)
        start = (page - 1) * QUESTIONS_PER_PAGE
        end = start + QUESTIONS_PER_PAGE
        questions = [question.format() for question in selection]
        current_questions = questions[start:end]
        return current_questions
    
    def retrieve_questions(request, selection):
        try:
            questions = paginate_questions(request, selection)
            if len(questions) == 0: 
                raise Exception(NO_QUESTIONS_TO_SHOW_MESSAGE)
            all_categories = [category.format() for category in Category.query.all()]
            if len(all_categories) == 0:
                raise Exception(NO_CATEOGIRES_TO_SHOW_MESSAGE)
            categories_reg = {category["id"]: category["type"] for category in all_categories}
            categories = [category["type"] for category in all_categories]
            return jsonify(
                {
                    "success": True,
                    "questions": questions,
                    "total_questions": len(selection),
                    'current_category': categories,
                    "categories": categories_reg,
                }
            )
        except Exception as e:
            if e.__str__() == NO_QUESTIONS_TO_SHOW_MESSAGE:
                abort(404)
            elif e.__str__() == NO_CATEOGIRES_TO_SHOW_MESSAGE:
                abort(404)
            else:
                abort(422)

    @app.route("/questions")
    def retrieve_all_questions():
        selection = Question.query.order_by(Question.id).all()
        return retrieve_questions(request, selection)

    @app.route('/questions/<int:questionID>', methods=['DELETE'])
    def delete_question(questionID):
        try:
            question = Question.query.filter_by(id = questionID).first()
            if question is None:
                raise Exception(NO_QUESTION_FOUND_MESSAGE)
            question.delete()
            return jsonify({"success": True})
        except Exception as e:
            if e.__str__() == NO_QUESTION_FOUND_MESSAGE:
                abort(404)
            else:
                abort(422)

    @app.route('/questions', methods=['POST'])
    def questions_post_method():
        data = request.get_json()
        if "searchTerm" in data:
            searchTerm = data["searchTerm"]
            selection = Question.query.filter(Question.question.ilike("%" + searchTerm + "%")).all()
            return retrieve_questions(request, selection)
        elif ("question" in data) and ("answer" in data) and ("difficulty" in data) and ("category" in data):
            try:
                question = Question(
                    question = data["question"],
                    answer = data["answer"],
                    difficulty = data["difficulty"],
                    category = data["category"]
                )
                question.insert()
                return jsonify({"success": True, "id": question.id})
            except:
                abort(422)
        else:
            abort(400)
        
  
    @app.route("/categories/<int:category>/questions")
    def retrieve_questions_by_category(category):
        selection = Question.query.filter_by(category = category).all()
        return retrieve_questions(request, selection)

    @app.route("/quizzes", methods=['POST'])
    def play_game():
        data = request.get_json()
        try:
            category = int(data["quiz_category"]["id"])
            previous_questions = data["previous_questions"]
            questions = Question.query.filter(~Question.id.in_(previous_questions))
            if category != 0:
                categories = [c.format() for c in Category.query.all()]
                categoriesIds = [c["id"] for c in categories]
                if category in categoriesIds:
                    questions = questions.filter(Question.category == category)
                else:
                    raise Exception(INVALID_CATEGORY)
            questions = questions.all()
            if questions:
                return jsonify({'success': True, 'question': random.choice(questions).format()})
            else:
                return jsonify({'success': True})
        except Exception as e:
            if e.__str__() == INVALID_CATEGORY:
                abort(400)
            else:
                abort(422)

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"success": False, "error": 404, "message": "resource not found"}), 404

    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({"success": False, "error": 422, "message": "unprocessable"}), 422
        
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({"success": False, "error": 400, "message": "bad request"}), 400

    @app.errorhandler(405)
    def not_found(error):
        return jsonify({"success": False, "error": 405, "message": "method not allowed"}), 405

    return app

