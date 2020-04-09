import os


class NightLog(object):
    """
        During a night of observing with the Dark Energy Spectroscopic Instrument (DESI),
        observers are required to provide a detailed account of the events of the night.
        This tool provides observers with an interface to write the nightlog in the proper formatting.
    """

    def __init__(self,year,month,day):
        """
            Setup the nightlog framework for a given obsday.
        """
        self.obsday=year+month+day

    def get_started(self):
        self.os_dir="nightlogs/"+self.obsday+"/OperationsScientist/"
        self.qa_dir="nightlogs/"+self.obsday+"/DataQualityAssessment/"
        if not os.path.exists(self.os_dir):
            os.makedirs(self.os_dir)
        if not os.path.exists(self.qa_dir):
            os.makedirs(self.qa_dir)
        return print("Your obsday is "+self.obsday)


    def finish_the_night(self):
        # merge together all the different files into one .txt file to copy past on the set_cosmology
        # checkout the notebooks at https://github.com/desihub/desilo repository
