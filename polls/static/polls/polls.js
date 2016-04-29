/**
 * Created by Jurek on 3/21/2016.
 */
angular.module('pollsApp', ['ngRoute', 'ngResource'])
    .config(function($httpProvider, $interpolateProvider, $routeProvider, $resourceProvider) {
        $httpProvider.defaults.headers.common['X-Requested-With'] = 'XMLHttpRequest';
        $httpProvider.defaults.xsrfCookieName = 'csrftoken';
        $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';

        $interpolateProvider.startSymbol('[[');
        $interpolateProvider.endSymbol(']]');

        $routeProvider
            .when('/', {
                controller:'PollsController',
                templateUrl:'/static/polls/qlist.html'
            })
            .when('/view/:questionId', {
                controller:'ViewQuestionController',
                templateUrl:'/static/polls/qdetail.html'
            })
            .when('/results/:questionId', {
                controller:'ViewQuestionController',
                templateUrl:'/static/polls/qresults.html'
            })
            .otherwise({
                redirectTo:'/'
            });

        $resourceProvider.defaults.stripTrailingSlashes = false;
    })
    .controller('PollsController', function($scope, $http) {
        $scope.questions = [];
        $scope.loadQuestions = function() {
            $http.get('/polls/questions/latest/').success(function(data) {
                $scope.questions = data;
            });
        };

        $scope.loadQuestions();
    })
    .controller('ViewQuestionController', function($scope, $routeParams, $http, $q, $location) {
        $scope.question = undefined;
        $scope.selectedChoice = undefined;
        $scope.choices = [];
        $scope.loadQuestion = function() {
            $http.get('/polls/questions/' + $routeParams.questionId + '/').success(function(data) {
                $scope.question = data;
            });
        };
        $scope.loadChoices = function() {
            $http.get('/polls/choices/' + $routeParams.questionId + '/').success(function(data) {
                $scope.choices = data;
            });
        };
        $scope.loadData = function() {
            $scope.loadQuestion();
            $scope.loadChoices();
        };

        $scope.vote = function() {
            var deferred = $q.defer();
            $http.post('/polls/choices/' + $routeParams.questionId + '/' + $scope.selectedChoice + '/vote_for/')
                .success(function(data) {
                    deferred.resolve(true);
                    $location.path("/results/" + $routeParams.questionId);
                })
                .error(function() {
                    deferred.reject();
                    $location.path("/");
                });
            return deferred.promise;
        };

        $scope.loadData();
    });
