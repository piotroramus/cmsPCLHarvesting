angular
    .module('multirunApp', ['ui.bootstrap'])
    .controller('multirunController', MultirunController)

function MultirunController($scope, $http) {
    /* jshint validthis: true */
    var vm = this;

    vm.sortPredicate = 'creation_time';
    vm.sortReverse = true;  // most recent multirun first
    vm.filterMultiruns = ''; // display everything

    vm.multiruns = []
    vm.multirunsByWorkflow = []
    vm.splitByWorkflows = false;

    vm.currentPage = 1;
    vm.itemsPerPage = 25;
    vm.totalItems = 125;

    vm.chooseMultiruns = chooseMultiruns;
    vm.pageChanged = pageChanged;
    vm.refreshPage = refreshPage;
    vm.rowColor = rowColor;
    vm.sortBy = sortBy;
    vm.splitButtonText = splitButtonText;
    vm.switchView = switchView;
    vm.visibleCols = visibleCols;
    vm.eosDirValue = eosDirValue;

    vm.getMultiruns = getMultiruns;
    vm.getMultirunsByWorkflow = getMultirunsByWorkflow;

    vm.stateColors = {};
    vm.columns = {};


    function chooseMultiruns(multiruns) {
        /* the argument will be defined only when there is a split */
        return vm.splitByWorkflows ? multiruns : vm.multiruns;
    }

    function pageChanged() {
        if (vm.splitByWorkflows === true)
            vm.getMultirunsByWorkflow();
        else
            vm.getMultiruns();
    };

    function refreshPage() {
        location.reload();
    }

    function rowColor(state) {
        return {
            "background-color": vm.stateColors[state]
        };
    }

    function sortBy(sortPredicate) {
        vm.sortReverse = (vm.sortPredicate === sortPredicate) ? !vm.sortReverse : false;
        vm.sortPredicate = sortPredicate;
    };

    function splitButtonText() {
        var splitText = "Split by workflows";
        var doNotSplitText = "Do not split";
        return vm.splitByWorkflows ? doNotSplitText : splitText;
    }

    function switchView() {
        vm.splitByWorkflows = (vm.splitByWorkflows === true) ? false : true;
    }

    function visibleCols() {
        // 1 is for the button column which is not in the columns definitions
        // 2 is for runs column
        var visibleCounter = 2;
        for (var id in vm.columns)
            if (vm.columns[id]['show'] === true) visibleCounter++;
        return visibleCounter;
    }

    function eosDirValue(dir) {

        /*
        EOS dirs for multiruns have a following naming convention:

        PREFIX_0p_0f/ OR PREFIX/

        The goal is to sort them by the sum of the two numbers.
        The sum will always be different, because each time either of
        the two numbers is incremented.

        This approach sorts the dirs in the same order as they are
        produced by the system in time.
        */

        var pattern = /^.*_(\d*)p_(\d*)f\/$/g;
        var match = pattern.exec(dir);
        var sum = 0;
        if (match){
            // unary + operator converts string to a number
            sum = (+match[1]) + (+match[2]);
        }
        return sum;
    }

    function getMultiruns() {
        var murl = "/multiruns/?limit="+vm.itemsPerPage+"&offset="+(vm.currentPage-1)*vm.itemsPerPage
        $http({method: 'GET', url: murl})
            .success(function(data, status) {
                vm.multiruns = data['multiruns'];
                for (var i = 0; i < vm.multiruns.length; i++) {
                    vm.multiruns[i]["details"] = false;
                    vm.multiruns[i]["processing_times"] = parseProcessingTimes(vm.multiruns[i]["processing_times"]);
                    vm.multiruns[i]["creation_time"] = new Date(vm.multiruns[i]["creation_time"]);
                }
                vm.totalItems = data['total'];
            })
            .error(function(data, status) {
                console.error("Error while loading multiruns");
            })
    }

    function getMultirunsByWorkflow() {
        var murl = "/multiruns_by_workflow/?limit="+vm.itemsPerPage+"&offset="+(vm.currentPage-1)*vm.itemsPerPage
        $http({method: 'GET', url: murl})
            .success(function(data, status) {
                vm.multirunsByWorkflow = data['multiruns'];
                for (var workflow in vm.multirunsByWorkflow) {
                    for (var i = 0; i < vm.multirunsByWorkflow[workflow].length; i++) {
                        vm.multirunsByWorkflow[workflow][i]["details"] = false;
                        vm.multirunsByWorkflow[workflow][i]["processing_times"] = parseProcessingTimes(vm.multirunsByWorkflow[workflow][i]["processing_times"]);
                        vm.multirunsByWorkflow[workflow][i]["creation_time"] = new Date(vm.multirunsByWorkflow[workflow][i]["creation_time"]);
                    }
                }
            })
            .error(function(data, status) {
                console.error("Error while loading multiruns");
            })
    }

    function parseProcessingTimes(pt_json){
        // parses list of string dates into Date() objects
        var result = [];
        for (var t = 0; t < pt_json.length; t++){
            var attempt = {};
            var start_time = pt_json[t][0];
            var end_time = pt_json[t][1];
            // end_time can be null, but start_time can't
            attempt['start'] = new Date(start_time);
            attempt['end'] = null;
            if (end_time != null)
                attempt['end'] = new Date(end_time);
            result.push(attempt);
        }
        return result;
    };

    vm.stateColors = {
        'Need more data' : "#DCE775",
        'Ready' : "#81D4FA",
        'Processing' : "#80CBC4",
        'Processed OK' : "90CAF9",
        'Processing failed' : "#E57373",
        'DQM upload OK' : "#FFE082",
        'DQM upload failed' : "#CE93D8",
        'Dropbox upload failed' : "#F48FB1",
        'Uploads OK' : "#FFCC80",
    }

    vm.columns = {
        'id': {
            'name': 'ID',
            'show': true
        },
        'state': {
            'name': 'State',
            'show': true
        },
        'dataset': {
            'name': 'Dataset',
            'show': true
        },
        'number_of_events': {
            'name': 'Events',
            'show': true
        },
        'failure_retries': {
            'name': 'Failure Retries',
            'show': true
        },
        'no_payload_retries': {
            'name': 'No payload retries',
            'show': true
        },
        'perform_payload_upload': {
            'name': 'Payload upload',
            'show': false
        },
        'bfield': {
            'name': 'BField',
            'show': false
        },
        'cmssw': {
            'name': 'CMSSW',
            'show': false
        },
        'dropbox_log': {
            'name': 'Dropbox log URL',
            'show': false
        },
        'eos_dirs': {
            'name': 'EOS directories',
            'show': false
        },
        'global_tag': {
            'name': 'Global Tag',
            'show': false
        },
        'scram_arch': {
            'name': 'SCRAM architecture',
            'show': false
        },
        'scenario': {
            'name': 'Scenario',
            'show': false
        },
        'run_class_name': {
            'name': 'Run Class Name',
            'show': false
        },
        'processing_times': {
            'name': 'Processing Times',
            'show': false
        },
        'runs': {
            'name': 'Runs',
            'show': false
        },
        'creation_time': {
            'name': 'Creation time',
            'show': false
        }
    }
};