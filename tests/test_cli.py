from inventory_sim.cli import main


def test_doctor_reports_readiness(capsys) -> None:  # type: ignore[no-untyped-def]
    exit_code = main(["doctor"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Laboratory environment is ready." in output
    assert "version" in output


def test_demo_explains_current_status(capsys) -> None:  # type: ignore[no-untyped-def]
    exit_code = main(["demo"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "simulator has not been implemented yet" in output
    assert "Chapter 1" in output
