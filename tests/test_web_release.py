from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
WEB_ROOT = REPOSITORY_ROOT / "apps" / "web"


def test_hostinger_web_build_is_a_static_export():
    next_config = (WEB_ROOT / "next.config.ts").read_text()
    package_json = (WEB_ROOT / "package.json").read_text()

    assert 'output: "export"' in next_config
    assert "trailingSlash: true" in next_config
    assert "unoptimized: true" in next_config
    assert "prepare-hostinger-runtime" not in package_json
    assert not (WEB_ROOT / "proxy.ts").exists()
    assert not (WEB_ROOT / "app" / "api").exists()


def test_static_clerk_client_does_not_require_a_frontend_secret():
    package_json = (WEB_ROOT / "package.json").read_text()
    web_env_example = (WEB_ROOT / ".env.example").read_text()

    assert '"@clerk/react"' in package_json
    assert '"@clerk/nextjs"' not in package_json
    assert "NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY" in web_env_example
    assert "CLERK_SECRET_KEY" not in web_env_example


def test_sale_pages_and_legal_links_are_in_the_public_source_of_truth():
    seo_content = (WEB_ROOT / "lib" / "seo-content.ts").read_text()
    marketing_shell = (WEB_ROOT / "components" / "marketing-shell.tsx").read_text()

    for slug in (
        "pricing",
        "pilot",
        "contact",
        "privacy",
        "terms",
        "acceptable-use",
        "security",
    ):
        assert f'slug: "{slug}"' in seo_content

    for href in (
        "/contact/",
        "/privacy/",
        "/terms/",
        "/acceptable-use/",
    ):
        assert f'href="{href}"' in marketing_shell
