import psycopg2
import psycopg2.extras
import sys


class DbHandler(object):

    def __init__(self, db_name):
        super(DbHandler, self).__init__()
        self.db_name = db_name
        self.db = psycopg2.connect(self.db_name)
        cur = self.db.cursor()
        cur.execute(
            'CREATE TABLE IF NOT EXISTS "links" (id SERIAL PRIMARY KEY, hash VARCHAR(100), file_name VARCHAR(200), file_size INTEGER, message_id INTEGER);')

    def __format_cursor__(self):
        self.cursor = self.db.cursor(cursor_factory=psycopg2.extras.DictCursor)

    @staticmethod
    def _is_or_equals(value, always_equals=False):
        return ("=" if (value != "NULL" or always_equals) else " is ")

    @staticmethod
    def _value_or_null(value):
        return ("NULL" if value == "NULL" else ("'" + str(value) + "'"))

    def log(self, text, date=None, error=False, warning=False, info=False, debug=False):
        level = 0
        if (error):
            level = level + 3
        elif (warning):
            level = level + 2
        elif (info):
            level = level + 1
        elif (debug):
            level = level + 0

        if (date):
            fields = {'level': level, 'text': text, 'created_at': date}
        else:
            fields = {'level': level, 'text': text}
        return self.insert("logs", fields, log=False)

    def insert(self, table, values, updater=None, log=True):
        if (not updater):
            updater = values
        triple_template = "{0} {1} {2}"
        single_template = "{0}"

        try:
            updater_str = ', '.join([
                triple_template.format(
                    k,
                    self._is_or_equals(updater[k]),
                    self._value_or_null(updater[k])
                )
                for k in updater])

            values_str = ', '.join([
                triple_template.format(
                    k,
                    self._is_or_equals(values[k], always_equals=True),
                    self._value_or_null(values[k])
                )
                for k in values])

            columns_str = ', '.join([
                single_template.format(
                    k
                )
                for k in values])

            where_str = ' AND '.join([
                triple_template.format(
                    k,
                    self._is_or_equals(updater[k]),
                    self._value_or_null(updater[k])
                )
                for k in updater])
        except Exception as e:
            print("--values1")
            print(values)
            print("--updater2")
            print(updater)
            print("Line: " + str(sys.exc_info()[-1].tb_lineno))
            print(e)
            return 0

        exists = len(self.select(table, where_str, log=log))

        try:
            self.__format_cursor__()
        except Exception as e:
            print("Line: " + str(sys.exc_info()[-1].tb_lineno))
            print(e)
            return 0

        if (exists):
            sql = "UPDATE {0} SET {1} WHERE {2}".format(table, values_str, where_str)

            try:
                self.cursor.execute(sql)
                self.db.commit()
                return 2
            except Exception as e:
                print("Line: " + str(sys.exc_info()[-1].tb_lineno))
                print(e)
                return 0

        values2_str = ', '.join([
            single_template.format(
                self._value_or_null(values[k])
            )
            for k in values])

        sql = "INSERT INTO {0} ({1}) VALUES ({2})".format(table, columns_str, values2_str)

        try:
            # if (log):
            #     self.log("SQL: " + sql, debug=True)
            self.cursor.execute(sql)
            self.db.commit()
            return 1
        except Exception as e:
            print("Line: " + str(sys.exc_info()[-1].tb_lineno))
            print(e)
            return 0

    def select(self, table, where=None, log=True):
        if (where):
            sql = "SELECT '{0}' as type, * FROM {1} WHERE ({2})".format(table, table, where)
            # if (log):
            #     self.log("SQL: " + sql, debug=True)
            return self._selectRaw(sql)
        else:
            sql = "SELECT '{0}' as type, * FROM {1}".format(table, table)
            # if (log):
            #     self.log("SQL: " + sql, debug=True)
            return self._selectRaw(sql)

    def _selectRaw(self, sql):
        try:
            self.__format_cursor__()
            self.cursor.execute(sql)
            data = self.cursor.fetchall()
            return data
        except Exception as e:
            print("Line: " + str(sys.exc_info()[-1].tb_lineno))
            print(e)
            return False

    def delete(self, table, where=None, log=True):
        try:
            self.__format_cursor__()
            if (where):
                sql = "DELETE FROM {0} WHERE ({1})".format(table, where)
                # if (log):
                #     self.log("SQL: " + sql, debug=True)
                self.cursor.execute(sql)
            else:
                sql = "DELETE FROM {0}".format(table)
                # if (log):
                #     self.log("SQL: " + sql, debug=True)
                self.cursor.execute(sql)
            self.db.commit()
            return True
        except Exception as e:
            print(sql)
            return False
