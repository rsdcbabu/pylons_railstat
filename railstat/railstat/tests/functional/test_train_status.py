from railstat.tests import *

class TestTrainStatusController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='train_status', action='index'))
        # Test response...
