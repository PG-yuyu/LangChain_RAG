import os
import unittest


@unittest.skipUnless(
    os.getenv("NEO4J_CHROMA_RUN_INTEGRATION") == "1",
    "set NEO4J_CHROMA_RUN_INTEGRATION=1 and configure Neo4j/Chroma to run",
)
class Neo4jChromaIntegrationTest(unittest.TestCase):
    def test_real_clients_health_check(self):
        from neo4j_chroma.database_repository import DatabaseRepository
        from neo4j_chroma.vector_store import VectorStore

        self.assertIsInstance(DatabaseRepository.from_env().health_check(), bool)
        self.assertIsInstance(VectorStore.from_env().health_check(), bool)


if __name__ == "__main__":
    unittest.main()
