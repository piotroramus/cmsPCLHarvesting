angular.module('multirunApp', ['ui.bootstrap'])

.controller('multirunController', function($scope, $http) {

    /* jshint validthis: true */
    var vm = this;

    $scope.sortPredicate     = 'creation_time';
    $scope.sortReverse  = true;  // the 'newest' multirun first
    $scope.searchMultirun   = ''; // display everything

    $scope.multiruns = []
    $scope.multirunsByWorkflow = []
    $scope.splitByWorkflows = false;

    vm.currentPage = 1;
    vm.itemsPerPage = 25;
    vm.totalItems = 125;

    vm.pageChanged = function() {
        if ($scope.splitByWorkflows === true)
            $scope.getMultirunsByWorkflow();
        else
            $scope.getMultiruns();
    };

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

    $scope.getMultiruns = function() {
        var murl = "/multiruns/?limit="+vm.itemsPerPage+"&offset="+(vm.currentPage-1)*vm.itemsPerPage
        $http({method: 'GET', url: murl})
            .success(function(data, status) {
                $scope.multiruns = data['multiruns'];
                for (var i = 0; i < $scope.multiruns.length; i++) {
                    $scope.multiruns[i]["details"] = false;
                    $scope.multiruns[i]["processing_times"] = $scope.parseProcessingTimes($scope.multiruns[i]["processing_times"]);
                    $scope.multiruns[i]["creation_time"] = new Date($scope.multiruns[i]["creation_time"]);
                }
                vm.totalItems = data['total'];
            })
            .error(function(data, status) {
                console.error("Error while loading multiruns");
            })
    }

    $scope.getMultirunsByWorkflow = function() {
        var murl = "/multiruns_by_workflow/?limit="+vm.itemsPerPage+"&offset="+(vm.currentPage-1)*vm.itemsPerPage
        $http({method: 'GET', url: murl})
            .success(function(data, status) {
                $scope.multirunsByWorkflow = data['multiruns'];
                for (var workflow in $scope.multirunsByWorkflow) {
                    for (var i = 0; i < $scope.multirunsByWorkflow[workflow].length; i++) {
                        $scope.multirunsByWorkflow[workflow][i]["details"] = false;
                        $scope.multirunsByWorkflow[workflow][i]["processing_times"] = $scope.parseProcessingTimes($scope.multirunsByWorkflow[workflow][i]["processing_times"]);
                        $scope.multirunsByWorkflow[workflow][i]["creation_time"] = new Date($scope.multirunsByWorkflow[workflow][i]["creation_time"]);
                    }
                }
            })
            .error(function(data, status) {
                console.error("Error while loading multiruns");
            })
   }

    $scope.switchView = function() {
        $scope.splitByWorkflows = ($scope.splitByWorkflows === true) ? false : true;
    }

    $scope.sortBy = function(sortPredicate) {
        $scope.sortReverse = ($scope.sortPredicate === sortPredicate) ? !$scope.sortReverse : false;
        $scope.sortPredicate = sortPredicate;
    };

    $scope.parseProcessingTimes = function(pt_json){
        // parses list of string dates into Date() objects
        var result = [];
        for (var t = 0; t < pt_json.length; t++){
            var attempt = [];
            var start_time = pt_json[t][0];
            var end_time = pt_json[t][1];
            // end_time can be null, but start_time can't
            attempt.push(new Date(start_time));
            if (end_time == null)
                attempt.push(end_time)
            else
                attempt.push(new Date(end_time));
            result.push(attempt);
        }
        return result;
    };

    $scope.stateColors = {
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

    $scope.rowColor = function(state) {
        return {
            "background-color": $scope.stateColors[state]
        };
    }

    $scope.visibleCols = function() {
        // 1 is for the button column which is not in the columns definitions
        // 2 is for runs column
        var visibleCounter = 2;
        for (var id in vm.columns){

            if (vm.columns[id]['show'] === true) visibleCounter++;
        }
        return visibleCounter;
    }

});