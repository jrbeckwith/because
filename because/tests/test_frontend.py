from because.frontend import Frontend


class TestFrontend(object):
    def test_frontend_simple(self):
        frontend = Frontend("python", "local")
        assert frontend
