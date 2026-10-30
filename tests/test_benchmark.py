from benchmark import format_markdown_table, CaseBenchmarkResult


def test_format_markdown_table():
    sample_results = [
        CaseBenchmarkResult(
            case_id="01",
            name="case_01",
            category="Off-by-one",
            description="Sample bug",
            status="Fixed on 1st Attempt",
            latency_s=1.23,
            prompt_tokens=300,
            completion_tokens=100,
            total_tokens=400,
            notes="Resolved cleanly",
        ),
        CaseBenchmarkResult(
            case_id="02",
            name="case_02",
            category="Type Error",
            description="Sample type bug",
            status="Fixed within 3 Attempts (Attempt 2)",
            latency_s=2.45,
            prompt_tokens=600,
            completion_tokens=200,
            total_tokens=800,
            notes="Resolved on retry",
        ),
    ]

    table = format_markdown_table(sample_results)
    assert "| Case # | Bug Category |" in table
    assert "| 01 | Off-by-one |" in table
    assert "| 02 | Type Error |" in table
    assert "Fixed on First Attempt" in table
    assert "Fixed within 3 Attempts" in table
