from flask_restful import Api, Resource, reqparse
from flask import request
from checklist import api, db, models
import sys

class TaskResource(Resource):

	def put(self):

		if "name" not in request.form:
			return {"msg": "failed - missing 'name' field"}, 400

		name, comment, isToday, parent = [request.form.get(x) for x in ("name", "comment", "is_today", "parent")]
		isToday = True if isToday == "true" else False
		#parent will be True even if it is "0"
		parent = int(parent) if parent else None

		task = models.Task(name, comment, isToday, parent_task_id=parent)
		db.session.add(task)
		db.session.commit()

		view = task.createView()
		db.session.add(view)
		db.session.commit()

		return {"msg": "success", "data": {"task": {"id":task.id}}}

	def post(self):

		# taskID, name, comment, checked, isToday, parent = [
		# 	request.form.get(x) for x in ("id", "name", "comment", "checked", "is_today", "parent")
		# ]

		taskID = request.form.get("id")
		print request.form
		task = models.Task.query.filter_by(id=taskID).one()
		for x in ("name", "comment", ("parent", "parent_task_id")):
			if type(x) == tuple:
				attr = x[1]
				value = request.form.get(x[0])
			else:
				attr = x
				value = request.form.get(x)
			if value != None:
				value = True if value == "true" else False if value == "false" else value
				print attr, value
				setattr(task, attr, value)

		if request.form.get("checked") == "true" and not task.datetime_completed:
			task.markComplete(markDescendants=True)
		elif request.form.get("checked") == "false" and task.datetime_completed:
			task.datetime_completed = None

		db.session.commit()

		if request.form.get("view_index_delta"):
			try:
				viewIdDelta = int(request.form.get("view_index_delta"))
			except ValueError:
				return {"msg": "failed - view_id_delta must be integer"}, 400
		else:
			# task.updateView(0, True)
			viewIdDelta = 0

		column = None
		if request.form.get("is_today"):
			value = request.form.get("is_today")
			column = value = 0 if value == "true" else 1 if value == "false" else value
			try:
				value = int(value)
			except:
				return {"msg": "failed - is_today must be boolean or integer"}
			if value not in [0,1]:
				return {"msg": "failed - is_today must be boolean or integer"}

		print "updating view", column
		task.updateView(viewIdDelta, column=column, updateDescendants=True)

		db.session.commit()

		return {"msg": "success"}

	def delete(self):

		try:
			taskID = int(request.form.get("id"))
		except:
			return {"msg": "failed - 'id' field must be integer"}, 400

		task = models.Task.query.filter_by(id=taskID).one()
		try:
			task.deleteFromSession(deleteDescendants=True, deleteView=True)
			db.session.commit()
			return {"msg": "success"}
		except:
			print sys.exc_info()
			return {"msg": "failed - could not delete task"}, 500

api.add_resource(TaskResource, "/task")
