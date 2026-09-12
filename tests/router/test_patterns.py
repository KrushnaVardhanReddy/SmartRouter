from smartrouter.router.patterns import PatternRouter


def test_pattern_router_default_keywords():
    router = PatternRouter()

    # Should match default keywords using word boundaries
    assert router.is_nano_task("how to use git") is True
    assert router.is_nano_task("what is a bash script") is True
    assert router.is_nano_task("ls -la") is True

    # Case insensitive
    assert router.is_nano_task("GIT status") is True

    # Should not match substrings inside words
    assert router.is_nano_task("digital") is False  # 'git' inside 'digital'
    assert router.is_nano_task("abash") is False  # 'bash' inside 'abash'
    assert router.is_nano_task("pulse") is False  # 'ls' inside 'pulse'


def test_pattern_router_default_regex():
    router = PatternRouter()

    # Should match default regex
    assert router.is_nano_task("how to use grep in bash") is True

    # Case insensitive regex match
    assert router.is_nano_task("HOW TO USE ls IN BASH") is True

    # Script name match
    assert router.is_nano_task("script.sh") is True
    assert router.is_nano_task("my-script.bash") is True

    # Should not match
    assert router.is_nano_task("how to use python in windows") is False
    assert router.is_nano_task("script.py") is False


def test_pattern_router_custom_config():
    router = PatternRouter(keywords=["python", "java"], regex_patterns=[r"^error: .*"])

    # Match custom keywords
    assert router.is_nano_task("write a python script") is True
    assert router.is_nano_task("JAVA code") is True

    # Match custom regex
    assert router.is_nano_task("Error: null pointer") is True

    # Should not match defaults anymore
    assert router.is_nano_task("git status") is False
    assert router.is_nano_task("script.sh") is False


def test_pattern_router_empty_config():
    router = PatternRouter(keywords=[], regex_patterns=[])

    assert router.is_nano_task("git status") is False
    assert router.is_nano_task("script.sh") is False
    assert router.is_nano_task("anything") is False


def test_pattern_router_empty_text():
    router = PatternRouter()

    assert router.is_nano_task("") is False
    assert router.is_nano_task("   ") is False  # Doesn't match defaults
