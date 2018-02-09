function sigmoid(x) {
	return 1/(1+Math.exp(-x))
}

// The start & end point for input to the sigmoid function
var startX   = -5
var endX     =  5
var deltaX   = endX-startX

// Use the sigmoid function
smoothF = sigmoid

// The start & end values of the function
var startF = smoothF(startX)
var endF   = smoothF(endX)
var deltaF = endF-startF

// The duration, in ms, for the scroll
var duration = 500 

function smoothScroll(a) {
	console.log(a.hash);
	// remove the leading '#'
	var name = a.hash.substr(1)
	var selector = "a[name='"+name+"']"
	a.addEventListener("click", function(e) {
		e.preventDefault()
		var start = (new Date()).getTime()
		var pageOffset = window.pageYOffset
		var top = document.querySelector(selector).getBoundingClientRect().top
		window.setTimeout( function() { smoothMove(start,duration,pageOffset,top) } )
	}
	)
}

function smoothMove(start,duration,pageOffset,top) {
	var deltaT = (new Date()).getTime() - start
	if( deltaT<duration ) {
		// map from time to x : 0 to duration -> startX to endX
		var x = (deltaX/duration)*deltaT + startX

        // map from sigmoid to location : sigStart to sigEnd -> 0 to top
		var loc = (smoothF(x) - startF) * top / deltaF 

        // scroll
		window.scrollTo(0,pageOffset + loc)

        // scroll some more
		window.setTimeout( function() { smoothMove(start,duration,pageOffset,top) } )
	} else {
        // scroll to the final position
		window.scrollTo(0,pageOffset + top)
	}
}
