import logging
import os
import sys
import tempfile
import types
import unittest


def install_dependency_stubs():
    streamlit = types.ModuleType("streamlit")
    streamlit.error = lambda *args, **kwargs: None
    streamlit.info = lambda *args, **kwargs: None
    streamlit.warning = lambda *args, **kwargs: None
    streamlit.success = lambda *args, **kwargs: None
    streamlit.session_state = {}
    streamlit.secrets = {}
    sys.modules.setdefault("streamlit", streamlit)

    pymongo = types.ModuleType("pymongo")
    pymongo.MongoClient = object
    pymongo_errors = types.ModuleType("pymongo.errors")
    pymongo_errors.ConnectionFailure = Exception
    pymongo_errors.OperationFailure = Exception
    pymongo_errors.ServerSelectionTimeoutError = Exception
    sys.modules.setdefault("pymongo", pymongo)
    sys.modules.setdefault("pymongo.errors", pymongo_errors)

    embedding_service = types.ModuleType("utils.embedding_service")

    class FakeEmbeddingService:
        pass

    embedding_service.GeminiEmbeddingService = FakeEmbeddingService
    sys.modules.setdefault("utils.embedding_service", embedding_service)


install_dependency_stubs()

from utils.MongoDBFunctions import MongoDB


class LocalFallbackTest(unittest.TestCase):
    def make_db(self, path):
        db = MongoDB.__new__(MongoDB)
        db.logger = logging.getLogger("test-local-fallback")
        db.connection_active = False
        db._get_local_db_path = lambda: path
        return db

    def test_local_save_includes_unit_tests_and_searches_all_fields(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "local_db.json")
            db = self.make_db(path)

            saved = db._add_solution_locally(
                summary="A long enough summary about invoice processing and exception routing.",
                script="def run():\n    return 'processed'",
                block_diagram="flowchart TD",
                prerequisites="Requires approval-system credentials",
                domain="Finance",
                extra_info="Back office workflow",
                unit_tests="def test_run():\n    assert True",
            )

            self.assertTrue(saved)
            data = db._read_local_db()
            self.assertEqual(len(data), 1)
            self.assertTrue(data[0]["unit_tests"])
            self.assertNotEqual(data[0]["_id"], "1")

            script_results = db._search_local_db("processed")
            prereq_results = db._search_local_db("approval-system")
            test_results = db._search_local_db("test_run")

            self.assertEqual(len(script_results), 1)
            self.assertEqual(len(prereq_results), 1)
            self.assertEqual(len(test_results), 1)
            self.assertNotIn("score", data[0])


if __name__ == "__main__":
    unittest.main()
