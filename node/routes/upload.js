var multipart = require('connect-multiparty');
var multipartMiddleware = multipart();
var express = require('express');
var router = express.Router();
var fs = require('fs');

router.post('/', multipartMiddleware, function(req, res){
	console.log("Hello");

	var files = req.files;
	var body = req.body;
	var milliseconds = (new Date).getTime();
	console.log(milliseconds);
  		fs.createReadStream(files.files.path).pipe(fs.createWriteStream('../distributed/processing/' + milliseconds +'.mp4'));
		fs.unlink(files.files.path, function(err){
			if (err) throw err;
		});
		

	return res.json({
		success: true,
		message: "Registration successful!"

	
}); 
	
});


module.exports = router;