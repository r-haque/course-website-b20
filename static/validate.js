function validate(){
			var uname=document.getElementByID("uname");
			var password=document.getElementByID("pass");

			if(uname.value.trim()==""){
				alert("Blank Username");
				uname.style.border = "solid 2px red";
				document.getElementByID("luser")
				.style.visibility="visible";
				return false;
			}
			else if(password.value.trim()==""){
				alert("Blank Password");
				pass.style.border = "solid 2px red";
				document.getElementByID("lpass")
				.style.visibility="visible";
				return false;
			}
			else if(password.value.trim().length<5){
				alert("Password too short");
				return false;
			}
			else{
				return true;
			}
		}