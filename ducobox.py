from time import sleep
import re
import logging

log = logging.getLogger(__name__)


class DucoboxClient(object):

    def __init__(self, config):
        #TODO: something
        self.fail_retry_wait = 0.25
        self.read_timeout = 0.1

    def open(self):
        raise NotImplementedError("Abstract method")

    def close(self):
        raise NotImplementedError("Abstract method")

    def write(self, data):
        raise NotImplementedError("Abstract method")


    def read(self, timeout):
        raise NotImplementedError("Abstract method")


    def run_command(self, data, timeout=1, retry=5):
        """
        Execute a command and get the response

        retry if it fails
        """
        try:
            return self._run_command(data, timeout)
        except RuntimeError:
            if retry > 0:
                sleep(self.fail_retry_wait)
                return self.run_command(data, timeout, retry-1)
            raise


    def _run_command(self, data, timeout):
        """
        Execute a command and get the response

        raise an exception if it fails
        """
        self.write(data + "\r")
        result = list(self._read_response_lines(timeout))
        if data.strip() != result[0] or result[-1] != "" or \
                result[2] == "[WRN] CommDllPsiRf.c - line 516 : RX++" or \
                result[2] == "Failed":
            raise RuntimeError("Unexpected response")
        return result

    def _read_response_lines(self, timeout=1):
        line_splitter = re.compile(r'^(.*?)[\r\n]+')

        # Create a buffer for read data
        data = ""
        c_count = 0
        m_count = timeout / self.read_timeout
        while True:
            # Call the read method of the implementation
            n_data = self.read(self.read_timeout)
            if n_data == "":
                c_count += 1
                if c_count > m_count:
                    raise RuntimeError("Timeout in read")
            else:
                c_count = 0
            data += n_data
            if data == "> ":
                return
            # Find all the lines in the read data
            while True:
                m = line_splitter.match(data)
                if not m:
                    # There are no full lines yet, so we have to read some more
                    break
                data = data[m.end():]
                line = m.group(1).strip()
                yield line
