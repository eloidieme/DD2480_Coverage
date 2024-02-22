import time
from collections import defaultdict
from unittest import TextTestResult as _TextTestResult
from unittest import TextTestRunner

from scrapy.commands import ScrapyCommand
from scrapy.contracts import ContractsManager
from scrapy.utils.conf import build_component_list
from scrapy.utils.misc import load_object, set_environ

from scrapy.utils.logger import log_branch

class TextTestResult(_TextTestResult):
    def printSummary(self, start, stop):
        write = self.stream.write
        writeln = self.stream.writeln

        run = self.testsRun
        plural = "s" if run != 1 else ""

        writeln(self.separator2)
        writeln(f"Ran {run} contract{plural} in {stop - start:.3f}s")
        writeln()

        infos = []
        if not self.wasSuccessful():
            write("FAILED")
            failed, errored = map(len, (self.failures, self.errors))
            if failed:
                infos.append(f"failures={failed}")
            if errored:
                infos.append(f"errors={errored}")
        else:
            write("OK")

        if infos:
            writeln(f" ({', '.join(infos)})")
        else:
            write("\n")


class Command(ScrapyCommand):
    requires_project = True
    default_settings = {"LOG_ENABLED": False}

    def syntax(self):
        return "[options] <spider>"

    def short_desc(self):
        return "Check spider contracts"

    def add_options(self, parser):
        ScrapyCommand.add_options(self, parser)
        parser.add_argument(
            "-l",
            "--list",
            dest="list",
            action="store_true",
            help="only list contracts, without checking them",
        )
        parser.add_argument(
            "-v",
            "--verbose",
            dest="verbose",
            default=False,
            action="store_true",
            help="print contract tests for all spiders",
        )

    def run(self, args, opts):
        # load contracts
        contracts = build_component_list(self.settings.getwithbase("SPIDER_CONTRACTS"))
        
        func_name="Command.run"
        # conman = ContractsManager(load_object(c) for c in contracts)
        # rewrite for finding branch coverage
        contract_objects = []
        for c in contracts:
            log_branch(1,func_name)
            contract_objects.append(load_object(c))
        conman = ContractsManager(contract_objects)
        
        # runner = TextTestRunner(verbosity=2 if opts.verbose else 1)
        # rewrite for finding branch coverage
        if opts.verbose:
            log_branch(2,func_name)
            verbosity_level = 2
        else:
            log_branch(3,func_name)
            verbosity_level = 1

        runner = TextTestRunner(verbosity=verbosity_level)
        result = TextTestResult(runner.stream, runner.descriptions, runner.verbosity)

        # contract requests
        contract_reqs = defaultdict(list)

        spider_loader = self.crawler_process.spider_loader

        with set_environ(SCRAPY_CHECK="true"):
            for spidername in args or spider_loader.list():
                log_branch(4,func_name)
                spidercls = spider_loader.load(spidername)
                spidercls.start_requests = lambda s: conman.from_spider(s, result)

                tested_methods = conman.tested_methods_from_spidercls(spidercls)
                if opts.list:
                    log_branch(5,func_name)
                    for method in tested_methods:
                        log_branch(6,func_name)
                        contract_reqs[spidercls.name].append(method)
                elif tested_methods:
                    log_branch(7,func_name)
                    self.crawler_process.crawl(spidercls)

            # start checks
            if opts.list:
                log_branch(8,func_name)
                for spider, methods in sorted(contract_reqs.items()):
                    log_branch(9,func_name)
                    if not methods and not opts.verbose:
                        log_branch(10,func_name)
                        continue
                    print(spider)
                    for method in sorted(methods):
                        log_branch(11,func_name)
                        print(f"  * {method}")
            else:
                log_branch(12,func_name)
                start = time.time()
                self.crawler_process.start()
                stop = time.time()

                result.printErrors()
                result.printSummary(start, stop)
                self.exitcode = int(not result.wasSuccessful())
