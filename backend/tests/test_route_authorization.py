"""Guard the HTTP route-to-role policy against accidental public access."""
import unittest

from fastapi.routing import APIRoute

from app.main import app


PUBLIC = {
    ("GET", "/api/policy"),
    ("POST", "/api/corrections"),
    ("POST", "/api/corrections/{request_ref}/status"),
    ("POST", "/api/auth/register"),
    ("POST", "/api/auth/login"),
    ("POST", "/api/auth/reset-password"),
}
AUTHENTICATED = {
    ("GET", "/api/auth/me"),
    ("POST", "/api/auth/logout"),
    ("POST", "/api/cases"),
    ("POST", "/api/cases/upload"),
    ("GET", "/api/cases"),
    ("GET", "/api/processing-status"),
    ("GET", "/api/cases/{case_id}"),
    ("GET", "/api/cases/{case_id}/report"),
    ("GET", "/api/campaigns"),
}
INVESTIGATOR = {
    ("GET", "/api/corrections"),
    ("PATCH", "/api/corrections/{request_ref}"),
    ("POST", "/api/corrections/{request_ref}/apply"),
    ("POST", "/api/cases/{case_id}/retry-processing"),
    ("POST", "/api/cases/{case_id}/entities/{entity_id}/review"),
    ("POST", "/api/cases/{case_id}/evidence/{evidence_id}/review"),
    ("POST", "/api/cases/{case_id}/disposition"),
    ("POST", "/api/cases/{case_id}/link/refresh"),
    ("POST", "/api/cases/{case_id}/links/{link_id}/review"),
    ("GET", "/api/graph"),
    ("GET", "/api/evidence-corpus"),
    ("POST", "/api/evidence-corpus"),
}
REVIEWER = {
    ("GET", "/api/accounts"),
    ("PATCH", "/api/accounts/{account_id}/status"),
    ("POST", "/api/accounts/{account_id}/password-reset"),
    ("GET", "/api/dispositions/pending"),
    ("PATCH", "/api/dispositions/{disposition_id}/review"),
    ("POST", "/api/evidence-corpus/{record_id}/retire"),
}


class RouteAuthorizationContractTests(unittest.TestCase):
    def test_every_api_route_has_an_explicit_expected_access_class(self):
        expected = PUBLIC | AUTHENTICATED | INVESTIGATOR | REVIEWER
        actual = {
            (method, route.path)
            for route in app.routes
            if isinstance(route, APIRoute) and route.path.startswith("/api/")
            for method in route.methods or ()
        }
        self.assertEqual(actual, expected, f"unclassified API routes: {actual ^ expected}")

    def test_route_dependencies_match_the_documented_access_class(self):
        expected_classes = {
            **{route: "public" for route in PUBLIC},
            **{route: "authenticated" for route in AUTHENTICATED},
            **{route: "investigator" for route in INVESTIGATOR},
            **{route: "reviewer" for route in REVIEWER},
        }
        required_dependency = {
            "public": None,
            "authenticated": "current_user",
            "investigator": "require_investigator",
            "reviewer": "require_reviewer",
        }
        for route in app.routes:
            if not isinstance(route, APIRoute) or not route.path.startswith("/api/"):
                continue
            dependency_names = {
                getattr(dependency.call, "__name__", "")
                for dependency in route.dependant.dependencies
            }
            for method in route.methods or ():
                key = (method, route.path)
                with self.subTest(method=method, path=route.path):
                    required = required_dependency[expected_classes[key]]
                    auth_dependencies = dependency_names & {
                        "current_user", "require_investigator", "require_reviewer"
                    }
                    if required is None:
                        self.assertFalse(auth_dependencies)
                    else:
                        self.assertIn(required, auth_dependencies)


if __name__ == "__main__":
    unittest.main()
