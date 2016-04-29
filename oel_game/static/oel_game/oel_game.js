/**
 * Created by Jurek on 4/22/2016.
 */

function hide(n){var e=document.getElementById(n); if (e) e.style.display='none';}
function show(m){var e=document.getElementById(m); if (e) e.style.display='';}
function add_class(o,s){var e=document.getElementById(o); if (e) e.className+=" "+s;}
function remove_class(o,s){var e=document.getElementById(o); if (e) e.className= e.className.replace(new RegExp("\\b"+s+"\\b",''));}
function showTab(tab) {
    hide('gamepage');
    hide('gamelog');
    hide('chatlog');
    hide('seat0');
    hide('seat1');
    hide('seat2');
    hide('seat3');
    remove_class('tabgamepage', 'tabselected');
    remove_class('tabgamelog', 'tabselected');
    remove_class('tabchatlog', 'tabselected');
    remove_class('tabseat0', 'tabselected');
    remove_class('tabseat1', 'tabselected');
    remove_class('tabseat2', 'tabselected');
    remove_class('tabseat3', 'tabselected');
    show(tab);
    add_class('tab' + tab, 'tabselected');
}

angular.module('oelGameApp', ['ngRoute', 'ngResource'])
    .config(function($httpProvider, $interpolateProvider, $routeProvider, $resourceProvider) {
        $httpProvider.defaults.headers.common['X-Requested-With'] = 'XMLHttpRequest';
        $httpProvider.defaults.xsrfCookieName = 'csrftoken';
        $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';

        $interpolateProvider.startSymbol('[[');
        $interpolateProvider.endSymbol(']]');

        $routeProvider
            .when('/', {
                controller:'GamesController',
                templateUrl:'/static/oel_game/gameslist.html'
            })
            .when('/view/:gameId', {
                controller:'ViewGameController',
                controllerAs:'app',
                templateUrl:'/static/oel_game/gamedetail.html'
            })
            .otherwise({
                redirectTo:'/'
            });

        $resourceProvider.defaults.stripTrailingSlashes = false;
    })
    .filter('orderObjectBy', function() {
        return function(items, field, reverse) {
            var filtered = [];
            angular.forEach(items, function(item) {
                filtered.push(item);
            });
            filtered.sort(function (a, b) {
                return (a[field] > b[field] ? 1 : -1);
            });
            if(reverse)
                filtered.reverse();
            return filtered;
        };
    })
    .controller('GamesController', function($scope, $http) {
        $scope.games = [];
        $scope.loadGames = function() {
            $http.get('/game/games/').success(function(data) {
                $scope.games = data;
            });
        };

        $scope.loadGames();
    })
    .controller('ViewGameController', function($scope, $routeParams, $http, $q, $location) {
        showTab('');

        $scope.game = undefined;
        $scope.loadGame = function() {
            $http.get('/game/games/' + $routeParams.gameId + '/').then(function(res) {
                $scope.game = res.data;
                showTab('gamepage');
            });
        };
        $scope.loadData = function() {
            $scope.loadGame();
        };

        this.render_seats = function() {
            console.log("Rendering Seat's canvas");
            for (var i=0; i<$scope.game.seats.length; i++) {
                console.log(document.getElementById("board_" + i));
            }
        };

        $scope.hide = hide;
        $scope.show = show;
        $scope.add_class = add_class;
        $scope.remove_class = remove_class;
        $scope.showTab = showTab;
        $scope.sortLandscapes = function(landscape) {
            return landscape;
        };
        $scope.sortBuildingMaterials = function(good) {
            switch (good.name) {
                case "wood": return "a";
                case "clay": return "b";
                case "stone": return "c";
                case "straw": return "d";
                case "coin": return "e";
                default: return "f" + good.name; // Just in case.  Sort alphabetically after the other main resources
            }
        };

        $scope.loadData();
    })
    .directive('seat_drawer', function() {
        return {
            restrict: 'A',
            scope: {
                data: '='
            },
            link: function(scope, element, attrs) {
                console.log("Inside link");
            }
        }
    });
