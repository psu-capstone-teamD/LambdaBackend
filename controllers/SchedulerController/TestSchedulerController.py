import unittest
from SchedulerController import SchedulerController


class MyTestCase(unittest.TestCase):
    def test_storebxffile_wrong_filename(self):
        schedControl = SchedulerController()
        data = "This is some data to put into s3"
        print(schedControl.storebxffile(1, data))

    def test_storebxffile_wrong_filetype(self):
        schedControl = SchedulerController()
        print(schedControl.storebxffile('afilename.xml', 1))

    def test_storelivefile_wrong_filename(self):
        schedControl = SchedulerController()
        data = "This is some data to put into s3"
        print(schedControl.storelivefile(1, data))

    def test_storelivefile_wrong_filetype(self):
        schedControl = SchedulerController()
        print(schedControl.storelivefile('afilename.xml', 1))

    def test_loadlivefile_wrong_filename(self):
        schedControl = SchedulerController()
        print(schedControl.loadLiveFile(1))

    def test_sendtolive_wrong_filename(self):
        schedControl = SchedulerController()
        print(schedControl.sendToLive(1))

    def test_inputxml_wrong_filetype(self):
        schedControl = SchedulerController()
        print(schedControl.inputxml(1))

    def test_inputxml_wrong_filetype_string(self):
        schedControl = SchedulerController()
        print(schedControl.inputxml(
            "<android.support.design.widget.AppBarLayout><android.support.v7.widget.Toolbar/></android.support.design.widget.AppBarLayout>"))

    def test_inputxml_is_filetype(self):
        schedControl = SchedulerController()
        data = "This is some data to put into s3"
        print(schedControl.inputxml(data))


if __name__ == '__main__':
    unittest.main()
