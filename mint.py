from flask import Flask
from flask_restplus import Api, Resource, fields, reqparse
from werkzeug.middleware.proxy_fix import ProxyFix 
import datetime
from datetime import date
from flask_mysqldb import MySQL


app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)
api = Api(app, version='1.0', title='TodoMVC API',
    description='A simple TodoMVC API',
)


#Database Configuration
app.config['MYSQL_USER'] = 'sql6412670'
app.config['MYSQL_PASSWORD'] = '9fTSdCmkNt'
app.config['MYSQL_HOST'] = 'sql6.freemysqlhosting.net'
app.config['MYSQL_DB'] = 'sql6412670'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'


mysql = MySQL(app)



#Initial Database initialisation
@app.route('/ind')
def index():
    cur = mysql.connection.cursor()
    cur.execute('''drop table taskstodo''')
    cur.execute('''create table taskstodo(id int(5) primary key,task varchar(25),due_date varchar(25),Status varchar(25))''')
    cur.execute('''insert into taskstodo values(1,'Task 1','01-01-2021','Not Started')''')
    cur.execute('''insert into taskstodo values(2,'Task 2','02-02-2021','Finished')''')
    cur.execute('''insert into taskstodo values(3,'Task 3','03-03-2021','In Progress')''')
    cur.execute('''select * from taskstodo''')
    results = cur.fetchall()
    cur.close()
    mysql.connection.commit()
    return str(results)



ns = api.namespace('todos', description='TODO operations')

#Model
todo = api.model('Todo', {
    'id': fields.Integer(readonly=True, description='The task unique identifier'),
    'task': fields.String(required=True, description='The task details'),
    'due_date': fields.String(required = True, description='Due date of the Task'),
    'Status': fields.String(required = True, desccription='Status of The Task')
})



#Adding Arguments
task_put_args = reqparse.RequestParser()
task_put_args.add_argument("id", type = int, help = "ID is required", required = True)
task_put_args.add_argument("task", type = str, help = "Task are required", required = True)
task_put_args.add_argument("due_date", type = str, help = "Due date is required", required = True)
task_put_args.add_argument("Status", type = str, help = "Status is required", required = True)





class TodoDAO(object):
    def __init__(self):
        self.counter = 0
        self.todos = []

    def get(self, id):
        for todo in self.todos:
            if todo['id'] == id:
                return todo
        api.abort(404, "Todo {} doesn't exist".format(id))

    def create(self, data):
        todo = data
        todo['id'] = self.counter = self.counter + 1
        self.todos.append(todo)
        return todo


    def update(self, id, data):
        todo = self.get(id)
        todo.update(data)
        return todo

    def delete(self, id):
        todo = self.get(id)
        self.todos.remove(todo)


DAO = TodoDAO()
DAO.create({'task': 'Task 1','due_date':'01-01-2021','Status':'Not Started'})
DAO.create({'task': 'Task 2','due_date':'02-02-2021','Status':'Finished'})
DAO.create({'task': 'Task 3','due_date':'03-03-2021','Status':'In Progress'})
DAO.create({'task': 'Task 4','due_date':'04-04-2021','Status':'In Progress'})
DAO.counter = 4
#print(DAO.get(2))



@ns.route('/')
class TodoList(Resource):
    '''Shows a list of all todos, and lets you POST to add new tasks'''
    
    @ns.doc('list_todos')
    @ns.marshal_list_with(todo)
    def get(self):
        '''List all tasks'''
        cur = mysql.connection.cursor()
        cur.execute('''select * from taskstodo''')
        results = cur.fetchall()
        cur.close()
        mysql.connection.commit()
        #return [results] '''For database retrieval'''
        
        return DAO.todos

    @ns.doc('create_todo')
    @ns.expect(todo)
    @ns.marshal_with(todo, code=201)
    def post(self):
        '''Create a new task'''
        temp = DAO.create(api.payload)
        cur = mysql.connection.cursor()
        cur.execute('''insert into taskstodo values(%s,%s,%s,%s)''',(DAO.counter,api.payload['task'],api.payload['due_date'],api.payload['Status']))
        cur.execute('''select * from taskstodo where id = %d''' % DAO.counter)
        results = cur.fetchall()
        cur.close()
        mysql.connection.commit()
        return [results]

       
#Argument Parser for Status
parser = reqparse.RequestParser()
parser.add_argument('new_status',type=str)


@ns.route('/<int:id>')
@ns.response(404, 'Todo not found')
@ns.param('id', 'The task identifier')
class Todo(Resource):
    '''Show a single todo item and lets you delete them'''
    @ns.doc('get_todo')
    @ns.marshal_with(todo)
    def get(self, id):
        '''Fetch a given resource'''
        cur = mysql.connection.cursor()
        cur.execute('''select * from taskstodo where id = %s''' % id)
        results = cur.fetchall()
        cur.close()
        mysql.connection.commit()
        return [results]

    @ns.doc('delete_todo')
    @ns.response(204, 'Todo deleted')
    def delete(self, id):
        '''Delete a task given its identifier'''
        cur = mysql.connection.cursor()
        cur.execute('''delete from taskstodo where id = %s''' % id)
        cur.execute('''select * from taskstodo''')
        results = cur.fetchall()
        cur.close()
        mysql.connection.commit()
        DAO.delete(id)
        return 204

    @ns.expect(parser)
    @ns.response(204,'Todo Updated')
    def post(self,id):
        '''Update the Status of a Task'''
        args = parser.parse_args()
        cur = mysql.connection.cursor()
        cur.execute('''update taskstodo set Status = %s where id = %s''',(id,args['new_status']))
        results = cur.fetchall()
        cur.close()
        mysql.connection.commit()
        for todo in DAO.todos:
            if todo['id'] == id:
                todo['Status'] = args['new_status']
        return DAO.todos
        

    
    @ns.expect(todo)
    @ns.marshal_with(todo)
    def put(self, id):
        '''Update a task given its identifier'''
        cur = mysql.connection.cursor()
        cur.execute('''delete from taskstodo where id = %s''' % id)
        cur.execute('''insert into taskstodo values(%s,%s,%s,%s)''',(id,api.payload['task'],api.payload['due_date'],api.payload['Status']))
        results = cur.fetchall()
        cur.close()
        mysql.connection.commit()
        return DAO.update(id, api.payload)



@app.route('/GET/due/<string:due_date>')

def get(due_date):
    ret = []
    for todo in DAO.todos:
           if todo['due_date'] == due_date:
               ret.append(todo)
    return str(ret)

@app.route('/GET/overdue')

def geto():
    today = date.today()
    reto = []
    for todo in DAO.todos:
           format_str = '%d-%m-%Y' # The format
           datetime_obj = datetime.datetime.strptime(todo['due_date'], format_str) 
           if datetime_obj.date() < today and todo['Status'] != 'Finished':
               reto.append(todo)
    return str(reto)




@app.route('/GET/finished')

def getf():
    retf = []
    for todo in DAO.todos:
           if todo['Status'] == 'Finished' or todo['Status'] == 'finished':
               retf.append(todo)
    return str(retf)


if __name__ == '__main__':
    app.run(debug=True)
