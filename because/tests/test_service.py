from because.service import Service, Endpoint


class TestService(object):
    def test_service_simple(self):
        service = Service({
            "foo": Endpoint(
                "/foo",
            )
        })
        assert service
