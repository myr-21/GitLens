import unittest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock
from services.fusion import reciprocal_rank_fusion
from services.ranking import rank_repositories, compute_stars_score, compute_recency_score

class TestSuggesterBackend(unittest.TestCase):

    def test_reciprocal_rank_fusion(self):
        """Test that Reciprocal Rank Fusion correctly merges and ranks two search streams."""
        vector_results = [
            {"github_id": 1, "full_name": "owner/repo1", "similarity": 0.85},
            {"github_id": 2, "full_name": "owner/repo2", "similarity": 0.72},
        ]
        
        keyword_results = [
            {"github_id": 2, "full_name": "owner/repo2", "keyword_score": 1.5},
            {"github_id": 3, "full_name": "owner/repo3", "keyword_score": 0.8},
        ]
        
        # Merge results using RRF
        merged = reciprocal_rank_fusion(vector_results, keyword_results, k=60)
        
        # Check that we have exactly 3 unique repos merged
        self.assertEqual(len(merged), 3)
        
        # Verify rank updates
        repo2 = next(r for r in merged if r["github_id"] == 2)
        self.assertEqual(repo2["vector_rank"], 2)
        self.assertEqual(repo2["keyword_rank"], 1)
        self.assertEqual(repo2["vector_similarity"], 0.72)
        self.assertEqual(repo2["keyword_score"], 1.5)
        
        # Verify sorting by RRF score descending
        # repo 2 is in both, so it should have the highest RRF score
        self.assertEqual(merged[0]["github_id"], 2)

    def test_stars_score_calculation(self):
        """Test log10 based star score calculation."""
        # 100k stars should be maximum score (1.0)
        self.assertAlmostEqual(compute_stars_score(100000), 1.0, places=4)
        # 0 stars should be 0.0
        self.assertEqual(compute_stars_score(0), 0.0)
        # 100 stars should be log10(101)/log10(100k) = ~2.004 / 5 = ~0.40
        self.assertAlmostEqual(compute_stars_score(100), 0.40, places=2)
        # Check clamping
        self.assertEqual(compute_stars_score(250000), 1.0)

    def test_recency_score_calculation(self):
        """Test decay based recency score calculation."""
        # Check invalid date formats safely degrade
        self.assertEqual(compute_recency_score("invalid-date-format"), 0.0)
        
        # Check that a date in the past returns a valid decay score
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        yesterday_score = compute_recency_score(yesterday)
        
        # Yesterday should have a high score close to 1.0
        self.assertTrue(0.95 < yesterday_score <= 1.0)
        
        one_year_ago = (datetime.now(timezone.utc) - timedelta(days=365)).isoformat()
        one_year_score = compute_recency_score(one_year_ago)
        
        # 1 year ago should be roughly exp(-1) = ~0.368
        self.assertAlmostEqual(one_year_score, 0.368, places=2)

    def test_multi_factor_ranking(self):
        """Test final score and ranking matches the multi-factor formula."""
        merged_repos = [
            {
                "github_id": 1,
                "full_name": "test/repo-popular",
                "vector_similarity": 0.85,
                "keyword_score": 2.0, # Max keyword score
                "stars": 100000,      # Score: 1.0
                "updated_at": datetime.now(timezone.utc).isoformat() # Score: 1.0
            },
            {
                "github_id": 2,
                "full_name": "test/repo-obscure",
                "vector_similarity": 0.60,
                "keyword_score": 1.0, # Score relative to max = 0.5
                "stars": 9,           # Score: ~0.2
                "updated_at": (datetime.now(timezone.utc) - timedelta(days=365)).isoformat() # Score: ~0.368
            }
        ]
        
        ranked = rank_repositories(merged_repos)
        
        # Verify length and sort
        self.assertEqual(len(ranked), 2)
        self.assertEqual(ranked[0]["full_name"], "test/repo-popular")
        
        # Verify score math for test/repo-popular
        # Formula: 0.4 * semantic + 0.3 * keyword + 0.2 * stars + 0.1 * recency
        # = 0.4 * 0.85 + 0.3 * 1.0 (since max is 2.0 and score is 2.0) + 0.2 * 1.0 + 0.1 * 1.0
        # = 0.34 + 0.30 + 0.20 + 0.10 = 0.94
        self.assertAlmostEqual(ranked[0]["relevance_score"], 0.94, places=2)

if __name__ == "__main__":
    unittest.main()
