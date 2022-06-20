from crypt import methods
import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10
# paginate_questions


def paginate_questions(request, selection):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE
    questions = [question.format() for question in selection]
    current_questions = questions[start:end]
    return current_questions


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)

    """
    @TODO: Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
    """
    CORS(app)

    """
    @TODO: Use the after_request decorator to set Access-Control-Allow
    """
    @app.after_request
    def after_request(response):
        response.headers.add(
            'Access-Control-Allow-Headers',
            'Content-Type,Authorization,true')
        response.headers.add(
            'Access-Control-Allow-Methods',
            'GET,PUT,POST,DELETE,OPTIONS')
        return response

    """
    @TODO:
    Create an endpoint to handle GET requests
    for all available categories.
    """
    @app.route('/categories')
    def get_categories():
        categories = Category.query.all()
        categories_dic = {}
        for category in categories:
            categories_dic.update({category.id: category.type})

        return jsonify({
            'success': True,
            'categories': categories_dic
        })

    """
    @TODO:
    Create an endpoint to handle GET requests for questions,
    including pagination (every 10 questions).
    This endpoint should return a list of questions,
    number of total questions, current category, categories.

    TEST: At this point, when you start the application
    you should see questions and categories generated,
    ten questions per page and pagination at the bottom of the screen for three pages.
    Clicking on the page numbers should update the questions.
    """
    @app.route('/questions')
    def get_questions():
        selection = Question.query.all()
        current_questions = paginate_questions(request, selection)
        categories = Category.query.all()
        categories_list = {}
        for category in categories:
            categories_list.update({category.id: category.type})
        if len(current_questions) == 0:
            abort(404)
        return jsonify({
            'success': True,
            'questions': current_questions,
            'total_questions': len(Question.query.all()),
            'categories': categories_list,
            'current_category': None
        })

    """
    @TODO:
    Create an endpoint to DELETE question using a question ID.

    TEST: When you click the trash icon next to a question, the question will be removed.
    This removal will persist in the database and when you refresh the page.
    """
    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_question(question_id):
        question = Question.query.get(question_id)
        if question is None:
            abort(404)
        question.delete()

        return jsonify({
            'success': True,
            'deleted': question_id
        })

    # """
    # @TODO:
    # Create an endpoint to POST a new question,
    # which will require the question and answer text,
    # category, and difficulty score.

    # TEST: When you submit a question on the "Add" tab,
    # the form will clear and the question will appear at the end of the last page
    # of the questions list in the "List" tab.
    # """
    @app.route('/questions', methods=['POST'])
    def create_question():
        body = request.get_json()

        search_term = body.get('searchTerm', None)

        if search_term:
            selection = Question.query.filter(
                Question.question.ilike(
                    '%{}%'.format(search_term))).all()
            # current_questions = paginate_questions(request, selection)
            question_list = []
            for ques in selection:
                question_list.append(ques.format())

            return jsonify({
                'success': True,
                'questions': question_list,
                'total_questions': len(selection),
            })

        else:
            question = body.get('question')
            answer = body.get('answer')
            category = body.get('category')
            difficulty = body.get('difficulty')

            if question is None or answer is None or category is None or difficulty is None:
                abort(400)
            questionNew = Question(
                question=question,
                answer=answer,
                category=category,
                difficulty=difficulty)
            print(questionNew)
            questionNew.insert()

            return jsonify({
                'success': True,
                'created': questionNew.id,
                'question': questionNew.question,
                'answer': questionNew.answer,
                'category': questionNew.category,
                'difficulty': questionNew.difficulty
            })

    """
    @TODO:
    Create a POST endpoint to get questions based on a search term.
    It should return any questions for whom the search term
    is a substring of the question.

    TEST: Search by any phrase. The questions list will update to include
    only question that include that string within their question.
    Try using the word "title" to start.
    """
    # @app.route('/search', methods=['POST'])
    # def search_questions():
    #     body = request.get_json()
    #     search_term = body.get('searchTerm', None)
    #     if search_term is None:
    #         abort(400)

    #     # selection = Question.query.filter(Question.question.ilike('%' + search_term + '%')).all()
    #     selection = Question.query.filter(Question.question.ilike('%{}%'.format(search_term))).all()
    #     # current_questions = paginate_questions(request, selection)
    #     question_dic = {}
    #     for ques in selection:
    #         question_dic = ques.format()
    #     if len(selection) == 0:
    #         abort(404)
    #     return jsonify({
    #         'success': True,
    #         'questions': question_dic,
    #         'total_questions': len(selection),
    #     })

    """
    @TODO:
    Create a GET endpoint to get questions based on category.

    TEST: In the "List" tab / main screen, clicking on one of the
    categories in the left column will cause only questions of that
    category to be shown.
    """
    @app.route('/categories/<int:category_id>/questions')
    def get_questions_by_category(category_id):
        category = Category.query.get(category_id)
        if category is None:
            abort(404)
        selection = Question.query.filter(
            Question.category == category_id).all()
        current_questions = paginate_questions(request, selection)
        if len(current_questions) == 0:
            abort(404)
        return jsonify({
            'success': True,
            'questions': current_questions,
            'total_questions': len(selection),
            'current_category': category.type
        })

    """
    @TODO:
    Create a POST endpoint to get questions to play the quiz.
    This endpoint should take category and previous question parameters
    and return a random questions within the given category,
    if provided, and that is not one of the previous questions.

    TEST: In the "Play" tab, after a user selects "All" or a category,
    one question at a time is displayed, the user is allowed to answer
    and shown whether they were correct or not.
    """
    @app.route('/quizzes', methods=['POST'])
    def get_quiz_questions():

        body = request.get_json()
        previous_questions = body['previous_questions']
        quiz_category = body['quiz_category']['id']

        if quiz_category == 0:
            selection = Question.query.all()

        # catagory id is not found
        if Category.query.get(quiz_category) is None:
            abort(404)

        else:
            # if previous_questions is None:
            selection = Question.query.filter(
                Question.category == quiz_category).all()

        if previous_questions is None:
            question = selection[random.randrange(0, len(selection))].format()
        else:
            question = None
            for ques in selection:
                if ques.id not in previous_questions:
                    question = ques.format()
                    break
            if question is None:
                question = selection[random.randrange(
                    0, len(selection))].format()
        return jsonify({
            'success': True,
            'question': question
        })

    """
    @TODO:
    Create error handlers for all expected errors
    including 404 and 422.
    """
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "success": False,
            "error": 404,
            "message": "Resource not found"
        })

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            "success": False,
            "error": 400,
            "message": "Bad request"
        })

    @app.errorhandler(422)
    def unprocessable(error):
        return ({
            "success": False,
            "error": 422,
            "message": "unprocessable"
        })

    @app.errorhandler(500)
    def unprocessable(error):
        return ({
            "success": False,
            "error": 500,
            "message": "Internal server error"
        })

    return app
