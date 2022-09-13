import os
from unicodedata import category
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10
#Implement Pagination
def paginate_questions(request,selection):
    page=request.args.get("page",1,type=int)
    start=(page-1)*QUESTIONS_PER_PAGE
    end=start+QUESTIONS_PER_PAGE

    questions=[question.format() for question in selection]
    current_questions=questions[start:end]

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
            "Access-Control-Allow-Headers", "Content-Type,Authorization,true"
        )
        response.headers.add(
            "Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS"
        )
        return response
    """
    @TODO:
    Create an endpoint to handle GET requests
    for all available categories.
    """
    @app.route('/categories',methods=['GET'])
    def get_all_categories():
        # get all categories
        categories = Category.query.all()
        # categories dict for holding the retrives categories
        categoriesDict = {}

        # adding all categories to the dict
        for category in categories:
            categoriesDict[category.id] = category.type

        return jsonify({
            'success': True,
            'categories': categoriesDict
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
    @app.route('/questions',methods=['GET'])
    def retrieve_questions():
        try:

            selection=Question.query.order_by(Question.id).all()
            current_questions=paginate_questions(request, selection)

            if len(current_questions)==0:
                abort(404)

            categories=Category.query.all()
            hold={}
            for category in categories:
                hold[category.id]=category.type

            return jsonify(
                {
                    "success":True,
                    "questions":current_questions,
                    "total_questions":len(selection),
                    "categories":hold,
                    "currentCategory":"History"
                }
            )
        except:
            abort(400)

    """
    @TODO:
    Create an endpoint to DELETE question using a question ID.

    TEST: When you click the trash icon next to a question, the question will be removed.
    This removal will persist in the database and when you refresh the page.
    """
    @app.route("/questions/<int:question_id>",methods=['DELETE'])
    def delete_question(question_id):
        try:
            question=Question.query.filter_by(id=question_id).one_or_none()
            if question is None:
                abort(404)

            question.delete()
            selection=Question.query.order_by(Question.id).all()
            current_questions=paginate_questions(request,selection)
            return jsonify(
                {
                    "success":True,
                    "deleted":question_id,
                    "questions":current_questions,
                    "total_questions":len(selection)

                }
            )
        except:
            abort(404)
    """
    @TODO:
    Create an endpoint to POST a new question,
    which will require the question and answer text,
    category, and difficulty score.

    TEST: When you submit a question on the "Add" tab,
    the form will clear and the question will appear at the end of the last page
    of the questions list in the "List" tab.
    """
    @app.route('/questions',methods=['POST'])
    def create_question():
        body=request.get_json()

        new_question=body.get("question",None)
        new_answer=body.get("answer",None)
        new_category=body.get("category",None)
        new_difficulty=body.get("difficulty",None)
        if ((new_question =='') or (new_answer =='')or (new_category =='')or (new_difficulty =='')):
            abort(422)
        else:
            question=Question(
                question=new_question,
                answer=new_answer,
                category=new_category,
                difficulty=new_difficulty
                )
            question.insert()

            selection=Question.query.order_by(Question.id).all()
            current_questions=paginate_questions(request,selection)
            return jsonify(
                {
                    "success":True,
                    "created":question.id,
                    "questions":current_questions,
                    "total_questions":len(selection)
                }
            )
    """
    @TODO:
    Create a POST endpoint to get questions based on a search term.
    It should return any questions for whom the search term
    is a substring of the question.

    TEST: Search by any phrase. The questions list will update to include
    only question that include that string within their question.
    Try using the word "title" to start.
    """
    @app.route("/questions/search", methods=['POST'])
    def search():
        body = request.get_json()
        search = body.get('searchTerm')
        questions = Question.query.filter(
            Question.question.ilike('%'+search+'%')).all()

        if questions:
            currentQuestions = paginate_questions(request, questions)
            return jsonify({
                'success': True,
                'questions': currentQuestions,
                'total_questions': len(questions)
            })
        else:
            abort(404)
    """
    @TODO:
    Create a GET endpoint to get questions based on category.

    TEST: In the "List" tab / main screen, clicking on one of the
    categories in the left column will cause only questions of that
    category to be shown.
    """
    @app.route('/categories/<int:category_id>/questions',methods=['GET'])
    def get_questions_by_category(category_id):
        category=Category.query.filter_by(id=category_id).one_or_none()
        if category:
            questionInCategory=Question.query.filter_by(category=str(category_id)).all()
            current_questions=paginate_questions(request,questionInCategory)

            return jsonify(
                {
                    "success":True,
                    "questions":current_questions,
                    "total_questions":len(questionInCategory),
                    "currentCategory":category.type
                }
            )
        else:
            abort(404)
        
            
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
    @app.route('/quizzes',methods=['POST'])
    def quiz():
        # get the qestion category an the previous question
        body = request.get_json()
        quizCategory = body.get('quiz_category')
        previousQuestion = body.get('previous_questions')

        try:
            if (quizCategory['id'] == 0):
                questionsQuery = Question.query.all()
            else:
                questionsQuery = Question.query.filter_by(
                    category=quizCategory['id']).all()

            randomIndex = random.randint(0, len(questionsQuery)-1)
            nextQuestion = questionsQuery[randomIndex]

            stillQuestions = True
            while nextQuestion.id not in previousQuestion:
                nextQuestion = questionsQuery[randomIndex]
                return jsonify({
                    'success': True,
                    'question': {
                        "answer": nextQuestion.answer,
                        "category": nextQuestion.category,
                        "difficulty": nextQuestion.difficulty,
                        "id": nextQuestion.id,
                        "question": nextQuestion.question
                    },
                    'previousQuestion': previousQuestion
                })

        except:
            abort(404)
    """
    @TODO:
    Create error handlers for all expected errors
    including 404 and 422.
    """
    ############# Error handlers #############

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            "success": False,
            'error': 400,
            "message": "Bad request"
        }), 400

    @app.errorhandler(404)
    def page_not_found(error):
        return jsonify({
            "success": False,
            'error': 404,
            "message": "Page not found"
        }), 404

    @app.errorhandler(422)
    def unprocessable_recource(error):
        return jsonify({
            "success": False,
            'error': 422,
            "message": "Unprocessable resource"
        }), 422

    @app.errorhandler(500)
    def internal_server_error(error):
        return jsonify({
            "success": False,
            'error': 500,
            "message": "Internal server error"
        }), 500

    @app.errorhandler(405)
    def invalid_method(error):
        return jsonify({
            "success": False,
            'error': 405,
            "message": "Invalid method!"
        }), 405
    return app

