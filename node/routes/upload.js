var multipart = require('connect-multiparty');
var multipartMiddleware = multipart({ uploadDir: '/uploading'});
var express = require('express');
var router = express.Router();

router.post('/', multipartMiddleware, function(req, res){
	console.log("Hello");
	var files = req.files;
	console.log(files.upload.path);

});


module.exports = router;