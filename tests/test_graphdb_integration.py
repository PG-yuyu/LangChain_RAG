import os
import unittest


@unittest.skipUnless(
    os.getenv("GRAPHDB_RUN_INTEGRATION") == "1",
    "set GRAPHDB_RUN_INTEGRATION=1 and configure Neo4j/Chroma to run",
)
class GraphDBIntegrationTest(unittest.TestCase):
    def test_real_clients_health_check(self):
        from graphdb.database_repository import DatabaseRepository
        from graphdb.vector_store import VectorStore

        self.assertIsInstance(DatabaseRepository.from_env().health_check(), bool)
        self.assertIsInstance(VectorStore.from_env().health_check(), bool)


if __name__ == "__main__":
    unittest.main()
